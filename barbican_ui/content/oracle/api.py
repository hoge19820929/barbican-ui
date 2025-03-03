from openstack import connect
from openstack import connection
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