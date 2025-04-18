import boto3
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from openstack import resource
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes, serialization
from mistral_lib import actions

from barbican_ui.content.secrets import api as barbican_api

def get_kms_client(project_name, request=None):
    AWS_SECRET_NAME = '__AWS_Credentials'
    conn = None

    if request:
        secrets = barbican_api.get_secrets(request)
    else:
        conn = barbican_api.get_connection(project_name)
        secrets = conn.key_manager.secrets()
    
    for sec in secrets:
        if sec.name == AWS_SECRET_NAME:
            secret_id = sec.secret_id
            if request:
                secret = barbican_api.get_secret(request, secret_id)
            else:
                secret = conn.key_manager.get_secret(secret_id)
    
    if secret is None:
        return None
    
    aws_access_key_id = secret.payload.split(',')[0]
    aws_secret_access_key = secret.payload.split(',')[1]
    region_name = secret.payload.split(',')[2]

    session = boto3.Session(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=region_name,
    )

    return session.client('kms')

class KeyData(resource.Resource):
    resources_key = 'aws'
    base_path = '/aws'

    allow_create = True
    allow_fetch = True
    allow_commit = True
    allow_delete = True
    allow_list = True

    _query_mapping = resource.QueryParameters(
        "alias",
        "key_id",
        "key_state",
        "key_type",
        "key_spec",
        "key_usage",
        "source_key",
        "key_version",
        "aws_account",
        "region",
        "origin",
        "creation_date",
        "expiration_date"
    )

    alias = resource.Body('alias')
    key_id = resource.Body('key_id')
    key_state = resource.Body('key_state')
    key_type = resource.Body('key_type')
    key_spec = resource.Body('key_spec')
    key_usage = resource.Body('key_usage')
    source_key = resource.Body('source_key')
    key_version = resource.Body('key_version')
    aws_account = resource.Body('aws_account')
    region = resource.Body('region')
    origin = resource.Body('origin')
    creation_date = resource.Body('creation_date')
    expiration_date = resource.Body('expiration_date')

def get_key_alias(request, key_id):
    kms_client = get_kms_client(request.user.project_name, request)
    aliases = list_key_aliases(key_id, kms_client)
    if aliases is None:
        return None
    
    return aliases[0]

def list_kms_keys(kms_client):
    keys = []
    next_marker = None
    is_truncated = True

    while is_truncated:
        if next_marker:
            response = kms_client.list_keys(Marker=next_marker)
        else:
            response = kms_client.list_keys()

        keys.extend(response['Keys'])
        next_marker = response.get('NextMarker')
        is_truncated = response['Truncated']
    
    return keys

def describe_key_metadata(key_id, kms_client):
    response = kms_client.describe_key(KeyId=key_id)
    metadata = response['KeyMetadata']
    metadata['Region'] = kms_client.meta.region_name
    return metadata

def list_key_aliases(key_id, kms_client):
    response = kms_client.list_aliases(KeyId=key_id)
    aliases = [alias['AliasName'].replace('alias/', '') for alias in response['Aliases']]
    return aliases

def list_key_tags(key_id, kms_client):
    response = kms_client.list_resource_tags(KeyId=key_id)
    tags = {tag['TagKey']: tag['TagValue'] for tag in response['Tags']}
    return tags

def get_origin_key_id(key_id, kms_client):
    tags = list_key_tags(key_id, kms_client)

    return tags.get('OriginKeyID', None)

def determine_key_type(key_spec):
    symmetric_specs = [
        'SYMMETRIC_DEFAULT', 'HMAC_224', 'HMAC_256', 'HMAC_384', 'HMAC_512'
    ]
    asymmetric_specs = [
        'RSA_2048', 'RSA_3072', 'RSA_4096', 'ECC_NIST_P256', 'ECC_NIST_P384', 'ECC_NIST_P521',
        'ECC_SECG_P256K1', 'SM2'
    ]

    if key_spec in symmetric_specs:
        return 'SYMMETRIC'
    elif key_spec in asymmetric_specs:
        return 'ASYMMETRIC'
    else:
        return 'Unknown'

def fetch_key_data(key_id, kms_client):
    metadata = describe_key_metadata(key_id, kms_client)
    aliases = list_key_aliases(key_id, kms_client)

    is_system_key = any(alias.startswith('aws/') for alias in aliases)
    if is_system_key:
        return None
    
    # BYOKしたキーのみ表示
    tags = list_key_tags(key_id, kms_client)
    if 'OriginKeyID' not in tags:
        return None
    
    key_type = determine_key_type(metadata['KeySpec'])
    source_key = tags.get('OriginKeyName', '-')
    key_version = tags.get('OriginKeyVersion', '-')
    expiration_date = metadata.get('DeletionDate', '-')

    key_data = KeyData(
        id=metadata['KeyId'],
        alias=', '.join(aliases) if aliases else '-',
        key_id=metadata['KeyId'],
        key_state=metadata['KeyState'],
        key_type=key_type,
        key_spec=metadata['KeySpec'],
        key_usage=metadata['KeyUsage'],
        source_key=source_key,
        key_version=key_version,
        aws_account=metadata['AWSAccountId'],
        region=metadata['Region'],
        origin=metadata.get('Origin','-'),
        creation_date=metadata['CreationDate'].strftime('%Y-%m-%d %H:%M:%S') if 'CreationDate' in metadata else '-',
        expiration_date=expiration_date if expiration_date == '-' else expiration_date.strftime('%Y-%m-%d %H:%M:%S')
    )
    return key_data

def get_key_data_parallel(kms_client, keys, **filter):
    key_data_list = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_key_data, key['KeyId'], kms_client): key for key in keys}

        for future in as_completed(futures):
            result = future.result()
            if result:
                if not filter:
                    key_data_list.append(result)
                else:
                    for key, value in filter.items():
                        if result[key] == value:
                            key_data_list.append(result)
                        else:
                            continue
    
    return key_data_list

def get_secrets(request, **filter):
    kms_client = get_kms_client(request.user.project_name, request)
    keys = list_kms_keys(kms_client)
    key_data_list = get_key_data_parallel(kms_client, keys, **filter)

    return key_data_list

def kms_create_key(kms_client):
    response = kms_client.create_key(
        Origin='EXTERNAL',
        # TODO: 設定可能にする
        KeySpec='SYMMETRIC_DEFAULT'
    )
    return response['KeyMetadata']['KeyId']

def kms_get_import_parameters(kms_client, key_id):
    response = kms_client.get_parameters_for_import(
        KeyId=key_id,
        # TODO: 必要に応じて変更
        WrappingAlgorithm='RSAES_OAEP_SHA_1',
        WrappingKeySpec='RSA_2048'
    )
    return response['PublicKey'], response['ImportToken']

def encrypt_key_material(plaintext_key, wrapping_key_blob):
    # TODO: 必要に応じて変更
    wrapping_public_key = serialization.load_der_public_key(wrapping_key_blob)
    encrypt_key = wrapping_public_key.encrypt(
        plaintext_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA1()),
            algorithm=hashes.SHA1(),
            label=None
        )
    )
    return encrypt_key

def import_encrypted_key_material(kms_client, key_id, encrypted_key, import_token):
    kms_client.import_key_material(
        KeyId=key_id,
        EncryptedKeyMaterial=encrypted_key,
        ImportToken=import_token,
        ExpirationModel='KEY_MATERIAL_DOES_NOT_EXPIRE',
        #ExpirationModel='KEY_MATERIAL_EXPIRES',
        # TODO: GUIから設定できるようにする
        #ValidTo=datetime(2025, 6, 17, 12, 0, 0, tzinfo=timezone.utc)
    )

def create_alias(kms_client, key_id, alias_name):
    kms_client.create_alias(
        AliasName=alias_name,
        TargetKeyId=key_id
    )

def set_origin_tags(kms_client, key_id, secret_id, secret_name, secret_version):
    response = kms_client.tag_resource(
        KeyId=key_id,
        Tags=[
            {
                'TagKey': 'OriginKeyID',
                'TagValue': secret_id
            },
            {
                'TagKey': 'OriginKeyName',
                'TagValue': secret_name
            },
            {
                'TagKey': 'OriginKeyVersion',
                'TagValue': secret_version
            },
        ]
    )
    return response

def rotate_kms_key(kms_client, alias_name, new_id):
    kms_client.update_alias(
        AliasName=alias_name,
        TargetKeyId=new_id
    )

def get_key_id_from_alias(kms_client, alias_name):
    try:
        response = kms_client.describe_key(
            KeyId=alias_name
        )
        key_id = response['KeyMetadata']['KeyId']
        return key_id
    except Exception:
        return None

def byok_aws(project_name, key_name, alias_name, do_rotate, request=None, secret=None):
    if request:
        kms_client = get_kms_client(project_name, request)
        conn = barbican_api.create_connection(request)
    else:
        kms_client = get_kms_client(project_name)
        conn = barbican_api.get_connection(project_name)

    # キーのローテーションを行う場合、新しいシークレットを作成
    if do_rotate:
        key_id = get_key_id_from_alias(kms_client, alias_name)
        origin_key_id = get_origin_key_id(key_id, kms_client)

        if origin_key_id is None:
            secret = barbican_api.create_secret(conn, key_name)
        else:
            secret = barbican_api.create_new_version_secret(conn, origin_key_id)

    secret_id = secret.secret_id
    plaintext_key = secret.payload.encode()

    # ステップ 1: キーマテリアルなしで AWS KMS key を作成する
    key_id = kms_create_key(kms_client)

    if do_rotate:
        rotate_kms_key(kms_client, alias_name, key_id)
    else:
        create_alias(kms_client, key_id, alias_name)

    # ステップ 2: ラップパブリックキーおよびインポートトークンのダウンロード
    wrapping_key_blob, import_token = kms_get_import_parameters(kms_client, key_id)

    # ステップ 3: キーマテリアルを暗号化する
    encrypt_key = encrypt_key_material(plaintext_key, wrapping_key_blob)

    # ステップ 4: キーマテリアルのインポート
    import_encrypted_key_material(kms_client, key_id, encrypt_key, import_token)

    # Originのキー情報をタグに設定
    secret_version = barbican_api.get_key_version(conn, secret_id)
    set_origin_tags(kms_client, key_id, secret_id, secret.name, secret_version)

def schedule_key_deletion(request, key_id, waiting_period_days=7):
    kms_client = get_kms_client(request.user.project_name, request)

    response = kms_client.schedule_key_deletion(
        KeyId=key_id,
        PendingWindowInDays=waiting_period_days
    )
    return response

class BYOKAWSAction(actions.Action):
    def __init__(self, project_name, key_name, alias_name, do_rotate=False):
        self.project_name = project_name
        self.key_name = key_name
        self.alias_name = alias_name
        self.do_rotate = do_rotate

    def run(self, context):
        byok_aws(self.project_name, self.key_name, self.alias_name, self.do_rotate)

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
    - key_name
    - alias_name
    - do_rotate
  tasks:
    execute_byok_aws:
      action: byok.aws
      input:
        project_name: <% $.project_name %>
        key_name: <% $.key_name %>
        alias_name: <% $.alias_name %>
        do_rotate: <% $.do_rotate %>
      on-success: notify_execution
    notify_execution:
      action: std.echo output="byok_aws function executed successfully."
    """
    workflow = conn.workflow.create_workflow(
        definition=workflow_definition,
        scope='private',
    )

    return workflow

def create_cron_trigger(conn, workflow_name, project_name, key_name, alias_name, pattern):
    trigger = conn.workflow.create_cron_trigger(
        name=f'key_rotation_aws_{project_name}_{key_name}',
        workflow_name=workflow_name,
        workflow_input={
            "project_name": project_name,
            "key_name": key_name,
            "alias_name": alias_name,
            "do_rotate": True
        },
        pattern=pattern,
        remaining_executions=2  # 実行回数(開発中のみ設定)
    )
    return trigger

def auto_rotate_key(request, project_name, key_name, alias_name, pattern):
    conn = barbican_api.create_connection(request)
    workflow_name = f'rotate_workflow_aws_{project_name}'
    workflow_created = get_workflow(conn, workflow_name)
    if workflow_created is None:
        create_workflow(conn, workflow_name)

    trigger = create_cron_trigger(conn, workflow_name, project_name, key_name, alias_name, pattern)

    return trigger

def set_access_key(request, key_id, aws_secret, region):
    conn = barbican_api.create_connection(request)
    secret_data = f'{key_id},{aws_secret},{region}'

    conn.key_manager.create_secret(
        name='__AWS_Credentials',
        payload=secret_data,
        payload_content_type='text/plain',
        algorithm='AES',
        bit_length=256,
    )