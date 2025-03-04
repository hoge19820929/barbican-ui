import base64
import json
import oci
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from openstack import connect
from openstack import connection
from keystoneauth1.identity import v3
from keystoneauth1 import session

from barbican_ui.content.secrets import api as barbican_api

def create_vault(vault_client, compartment_id, display_name):
    # 同名のvaultがあれば作成しない
    existing_vaults = vault_client.list_vaults(compartment_id=compartment_id).data
    vault = next((v for v in existing_vaults if v.display_name == display_name), None)

    if not vault:
        vault_details = oci.key_management.models.CreateVaultDetails(
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

def import_key(manage_client, compartment_id, display_name, key_material):
    wrapped_import_key_json = {
        "wrappingAlgorithm": "RSA_OAEP_SHA256",
        "keyMaterial": key_material
    }

    key_shape = oci.key_management.models.KeyShape(
        algorithm="AES",
        length=32
    )

    # インポートの実行
    import_key_details = oci.key_management.models.ImportKeyDetails(
        compartment_id=compartment_id,
        display_name=display_name,
        key_shape=key_shape,
        wrapped_import_key=wrapped_import_key_json
    )

    imported_key = manage_client.import_key(import_key_details)

    return imported_key

def byok_oci(key_name, do_rotate=False):
    conn = barbican_api.get_connection()

    # キーのローテーションを行う場合、新しいシークレットを作成
    if do_rotate:
        secret = barbican_api.create_secret(conn, key_name)
    else:
        # 既存のシークレットを検索
        secrets = conn.key_manager.secrets()
        for sec in secrets:
            if sec.name == key_name:
                secret = sec
                # TODO: 要修正
                secret.payload = '0123456789abcdef0123456789abcdef'

    plaintext_key = secret.payload.encode()

    config = oci.config.from_file()
    compartment_id = config.get("compartment_id")

    vault_client = oci.key_management.KmsVaultClient(config)
    vault = create_vault(vault_client, compartment_id, key_name)

    service_endpoint = vault.management_endpoint

    manage_client = oci.key_management.KmsManagementClient(
        config=config,
        service_endpoint=service_endpoint
    )

    # キーマテリアルの作成
    key_material = create_key_material(manage_client, plaintext_key)

    # 鍵のインポート
    import_key(manage_client, compartment_id, key_name, key_material)

def id_uri_to_id(id_uri):
    return id_uri.rsplit('/', 1)[-1]

def create_session(request):
    auth_url = request.user.endpoint
    token = request.user.token.id
    project_id = request.user.project_id

    auth = v3.Token(
        auth_url=auth_url,
        token=token,
        project_id=project_id
    )

    sess = session.Session(auth=auth)
    return sess

def create_connection(request):
    sess = create_session(request)

    return connection.Connection(session=sess)

def get_connection():
    return connect(cloud='d_kms')

def get_secrets(request, **kwargs):
    conn = create_connection(request)

    return conn.key_manager.secrets(**kwargs)

def create_secret(conn, key_name):
    # TODO: 要修正
    secret = conn.key_manager.create_secret(
        name=key_name,
        # TODO: payload setting
        payload='0123456789abcdef0123456789abcdef',
        payload_content_type='text/plain',
        # TODO: algorithm selection
        algorithm='AES',
        bit_length=256,
    )

    return secret

def delete_secret(request, secret_id_uri):
    conn = create_connection(request)

    secret_id = id_uri_to_id(secret_id_uri)

    conn.key_manager.delete_secret(secret_id)