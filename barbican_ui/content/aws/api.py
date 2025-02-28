import boto3
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from openstack import resource
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes, serialization
from mistral_lib import actions

from barbican_ui.content.secrets import api as barbican_api

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
        "description",
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
    description = resource.Body('description')
    aws_account = resource.Body('aws_account')
    region = resource.Body('region')
    origin = resource.Body('origin')
    creation_date = resource.Body('creation_date')
    expiration_date = resource.Body('expiration_date')

def get_key_alias(key_id):
    kms_client = boto3.client('kms')

    response = kms_client.list_aliases()

    for alias in response['Aliases']:
        if 'TargetKeyId' in alias and alias['TargetKeyId'] == key_id:
            alias_name = alias['AliasName']

            if alias_name.startswith('alias/'):
                alias_name = alias_name[len('alias/'):]
            return alias_name
    
    return None

def list_kms_keys():
    kms_client = boto3.client('kms')
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
    
    key_type = determine_key_type(metadata['KeySpec'])
    expiration_date = metadata.get('DeletionDate', '-')

    key_data = KeyData(
        id=metadata['KeyId'],
        alias=', '.join(aliases) if aliases else '-',
        key_id=metadata['KeyId'],
        key_state=metadata['KeyState'],
        key_type=key_type,
        key_spec=metadata['KeySpec'],
        key_usage=metadata['KeyUsage'],
        description=metadata.get('Description', '-'),
        aws_account=metadata['AWSAccountId'],
        region=metadata['Region'],
        origin=metadata.get('Origin','-'),
        creation_date=metadata['CreationDate'].strftime('%Y-%m-%d %H:%M:%S') if 'CreationDate' in metadata else '-',
        expiration_date=expiration_date if expiration_date == '-' else expiration_date.strftime('%Y-%m-%d %H:%M:%S')
    )
    return key_data

def get_key_data_parallel(keys, **filter):
    kms_client = boto3.client('kms')

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_key_data, key['KeyId'], kms_client): key for key in keys}

        for future in as_completed(futures):
            result = future.result()
            if result:
                if not filter:
                    yield result
                else:
                    for key, value in filter.items():
                        if result[key] == value:
                            yield result
                        else:
                            continue

def get_secrets(**filter):
    keys = list_kms_keys()
    key_data_list = get_key_data_parallel(keys, **filter)

    return key_data_list

def kms_create_key(kms_client):
    response = kms_client.create_key(
        Origin='EXTERNAL',
        KeySpec='SYMMETRIC_DEFAULT'
    )
    return response['KeyMetadata']['KeyId']

def kms_get_import_parameters(kms_client, key_id):
    response = kms_client.get_parameters_for_import(
        KeyId=key_id,
        WrappingAlgorithm='RSAES_OAEP_SHA_1',
        WrappingKeySpec='RSA_2048'
    )
    return response['PublicKey'], response['ImportToken']

def encrypt_key_material(plaintext_key, wrapping_key_blob):
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
        ExpirationModel='KEY_MATERIAL_EXPIRES',
        ValidTo=datetime(2025, 6, 17, 12, 0, 0, tzinfo=timezone.utc)
    )

def create_alias(kms_client, key_id, alias_name):
    kms_client.create_alias(
        AliasName=alias_name,
        TargetKeyId=key_id
    )

def tag_kms_key_with_secret_id(kms_client, key_id, secret_id):
    response = kms_client.tag_resource(
        KeyId=key_id,
        Tags=[
            {
                'TagKey': 'OriginKeyID',
                'TagValue': secret_id
            },
        ]
    )
    return response

def add_description_to_key(kms_client, key_id, secret_id):
    metadata = kms_client.describe_key(KeyId=key_id)['KeyMetadata']

    current_description = metadata.get('Description', '')
    if current_description:
        new_description = f"{current_description} | secret_id: {secret_id}をインポート"
    else:
        new_description = f"secret_id: {secret_id}をインポート"
    
    response = kms_client.update_key_description(
        KeyId=key_id,
        Description=new_description
    )
    return response

def rotate_kms_key(kms_client, alias_name, new_id):
    kms_client.update_alias(
        AliasName=alias_name,
        TargetKeyId=new_id
    )

def byok_aws(key_name, alias_name, do_rotate=False):
    conn = barbican_api.get_connection()
    if do_rotate:
        secret = barbican_api.create_secret(conn, key_name)
    else:
        secrets = conn.key_manager.secrets()
        for sec in secrets:
            if sec.name == key_name:
                secret = sec
                secret.payload = '0123456789abcdef0123456789abcdef'

    secret_id = secret.secret_id
    plaintext_key = secret.payload.encode()

    kms_client = boto3.client('kms')
    key_id = kms_create_key(kms_client)

    if do_rotate:
        rotate_kms_key(kms_client, alias_name, key_id)
    else:
        create_alias(kms_client, key_id, alias_name)

    wrapping_key_blob, import_token = kms_get_import_parameters(kms_client, key_id)

    encrypt_key = encrypt_key_material(plaintext_key, wrapping_key_blob)

    import_encrypted_key_material(kms_client, key_id, encrypt_key, import_token)

    tag_kms_key_with_secret_id(kms_client, key_id, secret_id)

    add_description_to_key(kms_client, key_id, secret_id)

def schedule_key_deletion(key_id, waiting_period_days=7):
    kms_client = boto3.client('kms')

    response = kms_client.schedule_key_deletion(
        KeyId=key_id,
        PendingWindowInDays=waiting_period_days
    )
    return response

class BYOKAWSAction(actions.Action):
    def __init__(self, key_name, alias_name, do_rotate=False):
        self.key_name = key_name
        self.alias_name = alias_name
        self.do_rotate = do_rotate

    def run(self, context):
        byok_aws(self.key_name, self.alias_name, self.do_rotate)

def get_workflow(conn, name):
    workflows = conn.workflow.workflows()
    for workflow in workflows:
        if workflow.name == name:
            return workflow
    
    return None

def create_workflow(conn):
    workflow_definition = """
version: '2.0'
rotate_workflow:
  type: direct
  input:
    - key_name
    - alias_name
    - do_rotate
  tasks:
    execute_byok_aws:
      action: byok_aws_action.BYOKAWSAction
      input:
        key_name: <% $.key_name %>
        alias_name: <% $.alias_name %>
        do_rotate: <% $.do_rotate %>
      on-success: notify_execution
    notify_execution:
      action: std.echo output="byok_aws function executed successfully."
    """
    workflow = conn.workflow.create_workflow(
        definition=workflow_definition,
        scope='public',
    )

    return workflow

def create_cron_trigger(conn, workflow_name, key_name, alias_name):
    trigger = conn.workflow.create_cron_trigger(
        name=f'key_rotation_{key_name}',
        workflow_name=workflow_name,
        workflow_input={
            "key_name": key_name,
            "alias_name": alias_name,
            "do_rotate": True
        },
        pattern='* * * * *', # 1分毎に実行
        remaining_executions=2  # 実行回数(開発中のみ設定)
    )
    return trigger

def auto_rotate_key(key_name, alias_name):
    conn = barbican_api.get_connection()
    workflow_name = 'rotate_workflow'
    workflow_created = get_workflow(conn, workflow_name)
    if workflow_created is None:
        create_workflow(conn)
    trigger = create_cron_trigger(conn, workflow_name, key_name, alias_name)

    return trigger