import base64
from time import sleep
from datetime import datetime, timedelta, timezone
import oci
from oci.key_management import KmsVaultClient, KmsManagementClient
from oci.key_management.models import Key, KeyShape, ImportKeyDetails, ImportKeyVersionDetails
from oci.key_management.models import CreateVaultDetails, UpdateKeyDetails, ScheduleKeyDeletionDetails
import concurrent.futures
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from openstack import resource
from mistral_lib import actions

from barbican_ui.content.secrets import api as barbican_api

class KeyData(resource.Resource):
    resources_key = 'oracle'
    base_path = '/oracle'

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
        "key_state",
        "time_created",
        "origin_key_id",
    )

    name = resource.Body('name')
    key_id = resource.Body('key_id')
    key_version_count = resource.Body('key_version_count')
    vault_name = resource.Body('vault_name')
    key_state = resource.Body('key_state')
    time_created = resource.Body('time_created')
    origin_key_id = resource.Body('origin_key_id')

def fetch_keys_for_vault(vault, config, compartment_id):
    service_endpoint = vault.management_endpoint
    manage_client = KmsManagementClient(config, service_endpoint)
    keys = manage_client.list_keys(compartment_id).data

    key_data_list = []
    for key in keys:
        version_count = len(manage_client.list_key_versions(key.id).data)
        key_data = KeyData(
            id=vault.id + '/' + key.id,
            name=key.display_name,
            key_id=key.id,
            #key_version=manage_client.get_key(key.id).data.current_key_version,
            key_version_count=version_count,
            vault_name=vault.display_name,
            key_state=key.lifecycle_state,
            time_created=key.time_created,
            origin_key_id=key.freeform_tags.get('OriginKeyID', ''),
        )
        key_data_list.append(key_data)

    return key_data_list

def get_key_data(**search_opts):
    config = oci.config.from_file()
    compartment_id = config["compartment_id"]

    kms_vault_client = KmsVaultClient(config)
    vaults = kms_vault_client.list_vaults(compartment_id).data

    key_data_list = []

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_vault = {executor.submit(fetch_keys_for_vault, vault, config, compartment_id): vault for vault in vaults}
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

def get_kms_management_client(vault_id):
    config = oci.config.from_file()
    kms_vault_client = KmsVaultClient(config)
    vault = kms_vault_client.get_vault(vault_id).data

    return KmsManagementClient(config, vault.management_endpoint)

def list_vault_names():
    config = oci.config.from_file()
    compartment_id = config["compartment_id"]

    kms_vault_client = KmsVaultClient(config)
    vaults = kms_vault_client.list_vaults(compartment_id).data
    vault_names = [f'{vault.display_name} / {vault.id}' for vault in vaults]

    return vault_names

def create_vault(vault_client, compartment_id, display_name):
    vault_details = CreateVaultDetails(
        compartment_id=compartment_id,
        display_name=display_name,
        vault_type='DEFAULT'
    )
    vault = vault_client.create_vault(create_vault_details=vault_details).data

    return vault

def create_key_material(manage_client, key):
    # ラッピングキーの取得
    wrapping_key_response = manage_client.get_wrapping_key()
    wrapping_key_pem = wrapping_key_response.data.public_key

    # ラッピングキーの読み込み
    wrapping_key = serialization.load_pem_public_key(
        wrapping_key_pem.encode('utf-8'),
        backend=default_backend()
    )

    # ラッピングキーで暗号化
    wrapped_key = wrapping_key.encrypt(
        key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    key_material = base64.b64encode(wrapped_key).decode('utf-8')

    return key_material

def import_key(manage_client, compartment_id, display_name, key_material, origin_key_id):
    wrapped_import_key_json = {
        "wrappingAlgorithm": "RSA_OAEP_SHA256",
        "keyMaterial": key_material
    }

    key_shape = KeyShape(
        algorithm="AES",
        length=32
    )

    # インポートの実行
    import_key_details = ImportKeyDetails(
        compartment_id=compartment_id,
        display_name=display_name,
        key_shape=key_shape,
        wrapped_import_key=wrapped_import_key_json,
        freeform_tags={"OriginKeyID": origin_key_id}
    )

    imported_key = manage_client.import_key(import_key_details)

    return imported_key

def byok_oci(vault_id, key_name):
    conn = barbican_api.get_connection()

    # 既存のシークレットを検索
    secrets = conn.key_manager.secrets()
    for sec in secrets:
        if sec.name == key_name:
            secret = sec
            # TODO: 要修正
            secret.payload = '0123456789abcdef0123456789abcdef'

    plaintext_key = secret.payload.encode()

    config = oci.config.from_file()
    compartment_id = config["compartment_id"]
    manage_client = get_kms_management_client(vault_id)

    # キーマテリアルの作成
    key_material = create_key_material(manage_client, plaintext_key)

    # 鍵のインポート
    import_key(manage_client, compartment_id, key_name, key_material, secret.secret_id)

def import_key_version(manage_client, key_id, key_material, origin_key_id):
    wrapped_import_key_json = {
        "wrappingAlgorithm": "RSA_OAEP_SHA256",
        "keyMaterial": key_material
    }

    import_key_version_details = ImportKeyVersionDetails(
        wrapped_import_key=wrapped_import_key_json,
        freeform_tags={"OriginKeyID": origin_key_id}
    )

    res = manage_client.import_key_version(key_id, import_key_version_details)

    return res

def wait_for_key_rotation(manage_client, key_id):
    while True:
        key = manage_client.get_key(key_id).data
        if key.lifecycle_state == Key.LIFECYCLE_STATE_ENABLED:
            return key.lifecycle_state
        sleep(1)

def update_key_tags(manage_client, key_id, origin_key_id):
    update_key_details = UpdateKeyDetails(
        freeform_tags={"OriginKeyID": origin_key_id}
    )

    res = manage_client.update_key(key_id, update_key_details)
    return res

def rotate_key(vault_id, key_id):
    manage_client = get_kms_management_client(vault_id)
    key = manage_client.get_key(key_id).data

    conn = barbican_api.get_connection()
    version_count = len(manage_client.list_key_versions(key_id).data) + 1
    key_name = f'{key.display_name}_v{version_count}'
    origin_key = barbican_api.create_secret(conn, key_name)

    key_material = create_key_material(manage_client, origin_key.payload.encode())
    import_key_version(manage_client, key_id, key_material, origin_key.secret_id)

    # OriginKeyIDタグを更新
    wait_for_key_rotation(manage_client, key_id)
    update_key_tags(manage_client, key_id, origin_key.secret_id)

def delete_key(vault_id, key_id):
    manage_client = get_kms_management_client(vault_id)

    time_of_deletion = datetime.now(timezone.utc) + timedelta(days=7)
    delete_details = ScheduleKeyDeletionDetails(
        time_of_deletion=time_of_deletion
    )
    manage_client.schedule_key_deletion(key_id, delete_details)

class BYOKOracleAction(actions.Action):
    def __init__(self, vault_id, key_id):
        self.vault_id = vault_id
        self.key_id = key_id
    
    def run(self, context):
        rotate_key(self.vault_id, self.key_id)

def get_workflow(conn, name):
    workflows = conn.workflow.workflows()
    for workflow in workflows:
        if workflow.name == name:
            return workflow
    
    return None

def create_workflow(conn):
    workflow_definition = """
version: '2.0'
rotate_oracle_workflow:
  type: direct
  input:
    - vault_id
    - key_id
  tasks:
    execute_byok_oracle:
      action: byok.oracle
      input:
        vault_id: <% $.vault_id %>
        key_id: <% $.key_id %>
      on-success: notify_execution
    notify_execution:
      action: std.echo output="byok_oracle function executed successfully."
    """
    workflow = conn.workflow.create_workflow(
        definition=workflow_definition,
        scope='private',
    )

    return workflow

def create_cron_trigger(conn, workflow_name, vault_id, key_id, pattern):
    trigger = conn.workflow.create_cron_trigger(
        name=f'key_rotation_{key_id}',
        workflow_name=workflow_name,
        workflow_input={
            "vault_id": vault_id,
            "key_id": key_id
        },
        pattern=pattern,
        remaining_executions=2  # 実行回数(開発中のみ設定)
    )
    return trigger

def auto_rotate_key(vault_id, key_id, pattern):
    conn = barbican_api.get_connection()
    workflow_name = 'rotate_oracle_workflow'
    workflow_created = get_workflow(conn, workflow_name)
    if workflow_created is None:
        create_workflow(conn)
    trigger = create_cron_trigger(conn, workflow_name, vault_id, key_id, pattern)

    return trigger