import json
from openstack import connect, connection, resource
from keystoneauth1.identity import v3
from keystoneauth1 import session

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

class KeyData(resource.Resource):
    resources_key = 'secrets'
    base_path = '/secrets'

    allow_create = True
    allow_fetch = True
    allow_commit = True
    allow_delete = True
    allow_list = True

    _query_mapping = resource.QueryParameters(
        "name",
        "key_id",
        "key_version",
        "container_id",
        "key_state",
        "time_created",
    )

    name = resource.Body('name')
    key_id = resource.Body('key_id')
    key_version = resource.Body('key_version')
    container_id = resource.Body('container_id')
    key_state = resource.Body('key_state')
    time_created = resource.Body('time_created')

def get_secret_metadata(conn, secret_id):
    url = f'http://localhost/key-manager/v1/secrets/{secret_id}/metadata'
    res = conn.session.get(url)

    if res.text:
        return json.loads(res.text)["metadata"]
    
    return None

def set_secret_metadata(conn, secret_id, key, value):
    url = f'http://localhost/key-manager/v1/secrets/{secret_id}/metadata'
    body = {
        "key": key,
        "value": value
    }
    return conn.session.post(url, json=body)

def update_container(conn, container_id, secret_ref):
    url = f'http://localhost/key-manager/v1/containers/{container_id}/secrets'

    return conn.session.post(url, json=secret_ref)

def get_key_data(request, **kwargs):
    conn = create_connection(request)
    keys = conn.key_manager.secrets(**kwargs)

    key_data_list = []
    for key in keys:
        metadata = get_secret_metadata(conn, key.secret_id)
        if metadata is None:
            key_version = ''
            container_id = ''
        else:
            key_version = metadata.get('key_version', '')
            container_id = metadata.get('container_id', '')
        
        key_data = KeyData(
            id=key.secret_id,
            name=key.name,
            key_id=key.secret_id,
            key_version=key_version,
            container_id=container_id,
            key_state=key.status,
            time_created=key.created_at
        )
        key_data_list.append(key_data)
    
    return key_data_list

def get_secrets(request, **kwargs):
    conn = create_connection(request)

    return conn.key_manager.secrets(**kwargs)

def create_secret(conn, key_name, container = None):
    # キー作成
    secret = conn.key_manager.create_secret(
        name=key_name,
        # TODO: payload setting
        payload='0123456789abcdef0123456789abcdef',
        payload_content_type='text/plain',
        # TODO: algorithm selection
        algorithm='AES',
        bit_length=256,
    )

    # コンテナ作成(or 更新)
    secret_ref = {'name': secret.name, 'secret_ref': secret.secret_ref}
    if container is None:
        container = conn.key_manager.create_container(
            name=key_name,
            type='generic',
            secret_refs=[secret_ref],
        )
    else:
        update_container(conn, container.container_id, secret_ref)
        container = conn.key_manager.get_container(container.container_id)
    
    # メタデータにコンテナIDとキーバージョンを保存
    key_version = len(container.secret_refs)
    set_secret_metadata(conn, secret.secret_id, "container_id", container.container_id)
    set_secret_metadata(conn, secret.secret_id, "key_version", f"{key_version}")

    return secret

def create_new_version_secret(secret_id):
    conn = get_connection()
    secret = conn.key_manager.get_secret(secret_id)
    metadata = get_secret_metadata(conn, secret_id)
    if metadata is None:
        container = None
    else:
        container_id = metadata.get('container_id', None)
        if container_id is None:
            container = None
        else:
            container = conn.key_manager.get_container(container_id)

    return create_secret(conn, secret.name, container)

def delete_secret(request, secret_id_uri):
    conn = create_connection(request)

    secret_id = id_uri_to_id(secret_id_uri)

    conn.key_manager.delete_secret(secret_id)