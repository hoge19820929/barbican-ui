import os
from datetime import datetime
import concurrent.futures
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, keywrap, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from google.cloud import kms
from google.auth import default
from openstack import resource
from mistral_lib import actions

from barbican_ui.content.secrets import api as barbican_api

def get_project_id():
    _, project_id = default()

    if project_id is None:
        raise ValueError("Project ID could not be retrieved from the credentials.")
    
    return project_id

def list_key_ring_ids():
    project_id = get_project_id()
    # TODO: FIXME
    location_id = 'us-central1'

    client = kms.KeyManagementServiceClient()
    location_path = client.common_location_path(project_id, location_id)

    key_ring_ids = []
    for key_ring in client.list_key_rings(parent=location_path):
        key_ring_id = key_ring.name.split('/')[-1]
        key_ring_ids.append(key_ring_id)

    return key_ring_ids

def create_key_for_import(project_id, location_id, key_ring_id, crypto_key_id):
    client = kms.KeyManagementServiceClient()

    # TODO: FIXME
    purpose = kms.CryptoKey.CryptoKeyPurpose.ENCRYPT_DECRYPT
    algorithm = kms.CryptoKeyVersion.CryptoKeyVersionAlgorithm.GOOGLE_SYMMETRIC_ENCRYPTION
    protection_level = kms.ProtectionLevel.SOFTWARE
    key = {
        "purpose": purpose,
        "version_template": {
            "algorithm": algorithm,
            "protection_level": protection_level,
        },
    }

    key_ring_path = client.key_ring_path(project_id, location_id, key_ring_id)

    created_key = client.create_crypto_key(
        request={
            "parent": key_ring_path,
            "crypto_key_id": crypto_key_id,
            "crypto_key": key,
            "skip_initial_version_creation": True,
        }
    )

    return created_key

def create_import_job(project_id, location_id, key_ring_id, import_job_id):
    client = kms.KeyManagementServiceClient()

    key_ring_path = client.key_ring_path(project_id, location_id, key_ring_id)
    import_method = kms.ImportJob.ImportMethod.RSA_OAEP_3072_SHA1_AES_256
    protection_level = kms.ProtectionLevel.SOFTWARE
    import_job_params = {
        "import_method": import_method,
        "protection_level": protection_level,
    }

    client.create_import_job(
        {
            "parent": key_ring_path,
            "import_job_id": import_job_id,
            "import_job": import_job_params,
        }
    )

def import_manually_wrapped_key(project_id, location_id, key_ring_id, crypto_key_id, import_job_id, payload):
    client = kms.KeyManagementServiceClient()

    crypto_key_path = client.crypto_key_path(project_id, location_id, key_ring_id, crypto_key_id)
    import_job_path = client.import_job_path(project_id, location_id, key_ring_id, import_job_id)

    kwp_key = os.urandom(32)
    wrapped_target_key = keywrap.aes_key_wrap_with_padding(kwp_key, payload, default_backend())

    import_job = client.get_import_job(name=import_job_path)
    import_job_pub = serialization.load_pem_public_key(
        bytes(import_job.public_key_pem, "UTF-8"), default_backend()
    )

    wrapped_kwp_key = import_job_pub.encrypt(
        kwp_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA1()),
            algorithm=hashes.SHA1(),
            label=None
        ),
    )

    response = client.import_crypto_key_version(
        {
            "parent": crypto_key_path,
            "import_job": import_job_path,
            "algorithm": kms.CryptoKeyVersion.CryptoKeyVersionAlgorithm.GOOGLE_SYMMETRIC_ENCRYPTION,
            "rsa_aes_wrapped_key": wrapped_kwp_key + wrapped_target_key,
        }
    )

    # Set the imported key version as the primary version.
    new_version_name = response.name
    client.update_crypto_key_primary_version(
        request={
            "name": crypto_key_path,
            "crypto_key_version_id": new_version_name.split('/')[-1],
        }
    )

def update_label(crypto_key, label):
    client = kms.KeyManagementServiceClient()

    crypto_key.labels["origin_key_id"] = label

    client.update_crypto_key(
        {
            "crypto_key": crypto_key,
            "update_mask": {"paths": ["labels"]}
        }
    )

def get_rotation_crypto_key(project_id, location_id, key_ring_id, crypto_key_id):
    client = kms.KeyManagementServiceClient()
    crypto_key_path = client.crypto_key_path(project_id, location_id, key_ring_id, crypto_key_id)
    return client.get_crypto_key(name=crypto_key_path)

def byok_google(key_ring_id, key_id, do_rotate = False):
    project_id = get_project_id()
    # TODO: FIXME
    location_id = 'us-central1'
    import_job_id = f'byok_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    create_import_job(project_id, location_id, key_ring_id, import_job_id)

    conn = barbican_api.get_connection()

    if do_rotate:
        secret = barbican_api.create_secret(conn, key_id)
        # ローテーション対象のキーを取得
        crypto_key = get_rotation_crypto_key(project_id, location_id, key_ring_id, key_id)
    else:
        secrets = conn.key_manager.secrets()
        for sec in secrets:
            if sec.name == key_id:
                secret = sec
                # TODO: FIXME
                secret.payload = '0123456789abcdef0123456789abcdef'
        # Google KMSにキーバージョンが空のキーを作成
        crypto_key = create_key_for_import(project_id, location_id, key_ring_id, key_id)
    
    import_manually_wrapped_key(
        project_id, location_id, key_ring_id, key_id, import_job_id, secret.payload.encode('utf-8')
    )
    # ラベルにorigin_key_idを設定
    update_label(crypto_key, secret.secret_id)

class KeyData(resource.Resource):
    resources_key = 'google'
    base_path = '/google'

    allow_create = True
    allow_fetch = True
    allow_commit = True
    allow_delete = True
    allow_list = True

    _query_mapping = resource.QueryParameters(
        "name",
        "key_id",
        "key_version_count",
        "key_ring_id",
        "key_status",
        "time_created",
        "origin_key_id",
    )

    name = resource.Body('name')
    key_id = resource.Body('key_id')
    key_version_count = resource.Body('key_version_count')
    key_ring_id = resource.Body('key_ring_id')
    key_status = resource.Body('key_status')
    time_created = resource.Body('time_created')
    origin_key_id = resource.Body('origin_key_id')

def fetch_keys(client, key_ring_path):
    keys = client.list_crypto_keys(parent=key_ring_path)
    
    key_data_list = []

    for key in keys:
        # タグ情報に"origin_key_id"が含まれているキーのみ取得
        if 'origin_key_id' in (key.labels or {}):
            key_name = key.name.split('/')[-1]
            key_id = key.name
            version_count = len(list(client.list_crypto_key_versions(parent=key.name)))
            key_ring_id = key_ring_path.split('/')[-1]
            status = key.primary.state.name if key.primary else "UNSPECIFIED"
            create_time = key.create_time if key.create_time else "N/A"
            origin_key_id = key.labels.get('origin_key_id', '')

            key_data = KeyData(
                id=key_id,
                name=key_name,
                key_id=key_id,
                key_version_count=version_count,
                key_ring_id=key_ring_id,
                key_status=status,
                time_created=create_time,
                origin_key_id=origin_key_id,
            )
            key_data_list.append(key_data)

    return key_data_list

def get_key_data(**search_opts):
    client = kms.KeyManagementServiceClient()
    project_id = get_project_id()
    location_id = 'us-central1'
    location_path = client.common_location_path(project_id, location_id)
    key_rings = client.list_key_rings(parent=location_path)

    key_data_list = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_key_ring = {
            executor.submit(fetch_keys, client, key_ring.name): key_ring for key_ring in key_rings
        }
        for future in concurrent.futures.as_completed(future_to_key_ring):
            results = future.result()
            if search_opts:
                for result in results:
                    for key, value in search_opts.items():
                        if result[key] == value:
                            key_data_list.extend([result])
            else:
                key_data_list.extend(results)

    return key_data_list

def rotate_key(key_path):
    # KEY Path: projects/{project_id}/locations/{location_id}/keyRings/{key_ring_id}/cryptoKeys/{key_id}
    key_ring_id = key_path.split('/keyRings/')[1].split('/')[0]
    crypto_key_id = key_path.split('/cryptoKeys/')[1]
    byok_google(key_ring_id, crypto_key_id, True)

def delete_key_versions(key_path):
    client = kms.KeyManagementServiceClient()
    versions = client.list_crypto_key_versions(parent=key_path)

    for version in versions:
        if version.state in [
            kms.CryptoKeyVersion.CryptoKeyVersionState.DESTROYED,
            kms.CryptoKeyVersion.CryptoKeyVersionState.DESTROY_SCHEDULED,
        ]:
            continue

        client.destroy_crypto_key_version(name=version.name)

class BYOKGoogleAction(actions.Action):
    def __init__(self, key_id):
        self.key_id = key_id
    
    def run(self, context):
        rotate_key(self.key_id)

def get_workflow(conn, name):
    workflows = conn.workflow.workflows()
    for workflow in workflows:
        if workflow.name == name:
            return workflow
    
    return None

def create_workflow(conn):
    workflow_definition = """
version: '2.0'
rotate_google_workflow:
  type: direct
  input:
    - key_id
  tasks:
    execute_byok_google:
      action: byok.google
      input:
        key_id: <% $.key_id %>
      on-success: notify_execution
    notify_execution:
      action: std.echo output="byok_google function executed successfully."
    """
    workflow = conn.workflow.create_workflow(
        definition=workflow_definition,
        scope='private',
    )

    return workflow

def create_cron_trigger(conn, workflow_name, key_id, pattern):
    trigger = conn.workflow.create_cron_trigger(
        name=f'key_rotation_{key_id}',
        workflow_name=workflow_name,
        workflow_input={
            "key_id": key_id
        },
        pattern=pattern,
        remaining_executions=2  # 実行回数(開発中のみ設定)
    )
    return trigger

def auto_rotate_key(key_id, pattern):
    conn = barbican_api.get_connection()
    workflow_name = 'rotate_google_workflow'
    workflow_created = get_workflow(conn, workflow_name)
    if workflow_created is None:
        create_workflow(conn)
    trigger = create_cron_trigger(conn, workflow_name, key_id, pattern)

    return trigger