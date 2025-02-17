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

def get_secrets(request, **kwargs):
    sess = create_session(request)

    conn = connection.Connection(session=sess)

    return conn.key_manager.secrets(**kwargs)

def create_secret(request, key_name):
    sess = create_session(request)
    conn = connection.Connection(session=sess)

    secret = conn.key_manager.create_secret(
        name=key_name,
        # TODO: payload setting
        payload='0123456789abcdef0123456789abcdef',
        payload_content_type='text/plain'
        # TODO: algorithm selection
        algorithm='AES',
        bit_length=256,
    )

    return secret

def delete_secret(request, secret_id_uri):
    sess = create_session(request)
    conn = connection.Connection(session=sess)

    secret_id = id_uri_to_id(secret_id_uri)

    conn.key_manager.delete_secret(secret_id)