import base64
import json
import os
import subprocess
import configparser
import concurrent.futures
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, keywrap, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.keyvault import KeyVaultManagementClient
from azure.keyvault.keys import KeyClient, KeyType
from openstack import resource
from mistral_lib import actions

from barbican_ui.content.secrets import api as barbican_api

def create_kek(vault_name, key_name):
    credential = DefaultAzureCredential()
    key_client = KeyClient(vault_url=f'https://{vault_name}.vault.azure.net/', credential=credential)

    return key_client.create_key(
        name=key_name,
        key_type=KeyType.rsa_hsm,
        size=2048,
        key_operations=["import"]
    )

def get_key(vault_name, key_name):
    credential = DefaultAzureCredential()
    key_client = KeyClient(vault_url=f'https://{vault_name}.vault.azure.net/', credential=credential)

    return key_client.get_key(key_name)

def get_origin_key_id(vault_name, key_name):
    key = get_key(vault_name, key_name)

    return key.properties.tags.get('OriginKeyID', None)

def get_public_key(key):
    return rsa.RSAPublicNumbers(
        e=int.from_bytes(key.key.e, byteorder='big'),
        n=int.from_bytes(key.key.n, byteorder='big')
    ).public_key()

def wrap_key(target_key, kek_rsa):
    kek_aes = os.urandom(32)
    wrapped_key = kek_rsa.encrypt(
        kek_aes,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA1()),
            algorithm=hashes.SHA1(),
            label=None
        ),
    )

    wrapped_target_key = keywrap.aes_key_wrap_with_padding(
        kek_aes, target_key, default_backend()
    )

    ciphertext = wrapped_key + wrapped_target_key

    return base64.urlsafe_b64encode(ciphertext).decode('utf-8')

def generate_byok_package(key_id, wrapped_key):
    byok_package = {
        "schema_version": "1.0.0",
        "header": {
            "kid": key_id,
            "alg": "dir",
            "enc": "CKM_RSA_AES_KEY_WRAP"
        },
        "ciphertext": wrapped_key,
        "generator": "BYOK tool v1.0"
    }

    return json.dumps(byok_package)

def import_key_azure(vault_name, key_name, byok_str, origin_key_id):
    command = [
        'az', 'keyvault', 'key', 'import',
        '--vault-name', vault_name,
        '--name', key_name,
        '--byok-string', byok_str,
        '--ops', 'encrypt', 'decrypt',
        '--tags', f'OriginKeyID={origin_key_id}'
    ]

    return subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

def byok_azure(project_name, vault_name, key_name, origin_key_id, do_rotate=False):
    conn = barbican_api.get_connection(project_name)

    if do_rotate:
        if origin_key_id is None:
            secret = barbican_api.create_secret(conn, key_name)
        else:
            secret = barbican_api.create_new_version_secret(conn, origin_key_id)
    else:
        secret = conn.key_manager.get_secret(origin_key_id)

    # クライアントKMSの鍵を使うように要修正
    target_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    ).private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    KEK_NAME = 'KEKforBYOK2048'

    try:
        kek = get_key(vault_name, KEK_NAME)
    except Exception:
        kek = create_kek(vault_name, KEK_NAME)

    kek_rsa = get_public_key(kek)

    wrapped_key = wrap_key(target_key, kek_rsa)

    byok_str = generate_byok_package(kek.id, wrapped_key)

    import_key_azure(vault_name, key_name, byok_str, secret.secret_id)

class KeyData(resource.Resource):
    resources_key = 'azure'
    base_path = '/azure'

    allow_create = True
    allow_fetch = True
    allow_commit = True
    allow_delete = True
    allow_list = True

    _query_mapping = resource.QueryParameters(
        "name",
        "key_id",
        "key_version_count",
        "vault_name",
        "key_enabled",
        "time_created",
        "origin_key_id",
    )

    name = resource.Body('name')
    key_id = resource.Body('key_id')
    key_version_count = resource.Body('key_version_count')
    vault_name = resource.Body('vault_name')
    key_enabled = resource.Body('key_enabled')
    time_created = resource.Body('time_created')
    origin_key_id = resource.Body('origin_key_id')

def get_subscription_id(credentials_file='~/.azure/credentials'):
    credentials_file = os.path.expanduser(credentials_file)

    config = configparser.ConfigParser()

    config.read(credentials_file)

    return config.get('DEFAULT', 'subscription_id', fallback=None)

def list_vaults(credential):
    subscription_id = get_subscription_id()

    resource_client = ResourceManagementClient(credential, subscription_id)
    kv_client = KeyVaultManagementClient(credential, subscription_id)

    resource_groups = resource_client.resource_groups.list()

    vaults_list = []

    for rg in resource_groups:
        keyvaults = kv_client.vaults.list_by_resource_group(rg.name)
        vaults_list.extend(keyvaults)
    
    return vaults_list

def fetch_keys_for_vault(credential, vault):
    try:
        key_client = KeyClient(vault_url=vault.properties.vault_uri, credential=credential)

        keys = key_client.list_properties_of_keys()

        key_data_list = []

        for key_property in keys:
            key = key_client.get_key(key_property.name)

            # タグ情報に"OriginKeyID"が含まれているキーのみ取得
            if 'OriginKeyID' in (key.properties.tags or {}):
                version_count = sum(1 for _ in key_client.list_properties_of_key_versions(key.name))
                key_data = KeyData(
                    id=key.id,
                    name=key.name,
                    key_id=key.id,
                    key_version_count=version_count,
                    vault_name=vault.name,
                    key_enabled=key.properties.enabled,
                    time_created=key.properties.created_on,
                    origin_key_id=key.properties.tags.get('OriginKeyID', ''),
                )
                key_data_list.append(key_data)

        return key_data_list
    except Exception:
        # アクセス権限エラーを無視
        return []

def get_key_data(**search_opts):
    credential = DefaultAzureCredential()
    vaults = list_vaults(credential)

    key_data_list = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_vault = {executor.submit(fetch_keys_for_vault, credential, vault): vault for vault in vaults}
        for future in concurrent.futures.as_completed(future_to_vault):
            results = future.result()
            if search_opts:
                for result in results:
                    for key, value in search_opts.items():
                        if result[key] == value:
                            key_data_list.extend([result])
            else:
                key_data_list.extend(results)

    return key_data_list

def list_vault_names():
    credential = DefaultAzureCredential()
    vaults = list_vaults(credential)
    vault_names = [vault.name for vault in vaults]

    return vault_names

def rotate_key(project_name, key_id):
    # KEY ID: https://{VAULT_NAME}.vault.azure.net/keys/{KEY_NAME}
    url_without_protocol = key_id.split('//')[1]
    domain_and_path = url_without_protocol.split('/')
    vault_name = domain_and_path[0].split('.')[0]
    key_name = key_id.split('/keys/')[1].split('/')[0]
    origin_key_id = get_origin_key_id(vault_name, key_name)

    byok_azure(project_name, vault_name, key_name, origin_key_id, True)

def delete_key(key_id):
    credential = DefaultAzureCredential()
    # KEY ID: https://{VAULT_NAME}.vault.azure.net/keys/{KEY_NAME}
    key_client = KeyClient(vault_url=key_id.split('/keys/')[0], credential=credential)

    try:
        key_name = key_id.split('/keys/')[1].split('/')[0]
        delete_operation = key_client.begin_delete_key(key_name)
        # 削除完了を待つ
        return delete_operation.result()
    except Exception as e:
        print(f"Failed to delete key '{key_id}': {e}")
        raise

class BYOKAzureAction(actions.Action):
    def __init__(self, project_name, key_id):
        self.project_name = project_name
        self.key_id = key_id
    
    def run(self, context):
        rotate_key(self.project_name, self.key_id)

def get_workflow(conn, name):
    workflows = conn.workflow.workflows()
    for workflow in workflows:
        if workflow.name == name:
            return workflow
    
    return None

def create_workflow(conn, workflow_name):
    workflow_definition = f"""
version: '2.0'
{workflow_name}:
  type: direct
  input:
    - project_name
    - key_id
  tasks:
    execute_byok_azure:
      action: byok.azure
      input:
        project_name: <% $.project_name %>
        key_id: <% $.key_id %>
      on-success: notify_execution
    notify_execution:
      action: std.echo output="byok_azure function executed successfully."
    """
    workflow = conn.workflow.create_workflow(
        definition=workflow_definition,
        scope='private',
    )

    return workflow

def create_cron_trigger(conn, workflow_name, project_name, key_id, pattern):
    trigger = conn.workflow.create_cron_trigger(
        name=f'key_rotation_{key_id}',
        workflow_name=workflow_name,
        workflow_input={
            "project_name": project_name,
            "key_id": key_id
        },
        pattern=pattern,
        remaining_executions=2  # 実行回数(開発中のみ設定)
    )
    return trigger

def auto_rotate_key(project_name, key_id, pattern):
    conn = barbican_api.get_connection(project_name)
    workflow_name = f'rotate_workflow_azure_{project_name}'
    workflow_created = get_workflow(conn, workflow_name)
    if workflow_created is None:
        create_workflow(conn, workflow_name)
    trigger = create_cron_trigger(conn, workflow_name, project_name, key_id, pattern)

    return trigger