from django.shortcuts import render, redirect
from django.contrib import messages
from openstack import connection
from .forms import CreateKeyForm

def create_key(request):
    """
    AES 256ビット鍵をBarbicanで作成するビュー
    """
    if request.method == 'POST':
        form = CreateKeyForm(request.POST)
        if form.is_valid():
            try:
                # Horizonの認証情報を使用
                auth_url = request.user.endpoint
                user_name = request.user.username
                password = request.session.get('password')  # セッションからパスワード取得

                # Barbican接続
                conn = connection.Connection(
                    auth_url=auth_url,
                    username=user_name,
                    password=password,
                    project_name=request.user.project_name,
                    user_domain_name='default',
                    project_domain_name='default'
                )

                # フォームデータ取得
                key_name = form.cleaned_data['key_name']
                key_description = form.cleaned_data['key_description']

                # 鍵作成
                key_data = b'0' * 32  # 256ビット（32バイト）の鍵データ
                conn.key_manager.create_secret(
                    name=key_name,
                    payload=key_data,
                    payload_content_type='application/octet-stream',
                    algorithm='AES',
                    bit_length=256,
                    mode='cbc',
                    description=key_description
                )

                messages.success(request, f"鍵 '{key_name}' を作成しました。")
                return redirect('barbican_ui:list_secrets')
            except Exception as e:
                messages.error(request, f"鍵作成時にエラー: {e}")
    else:
        form = CreateKeyForm()

    return render(request, 'barbican_ui/create_key.html', {'form': form})


def list_secrets(request):
    """
    Barbicanから鍵の一覧を取得して表示するビュー
    """
    try:
        # Horizonの認証情報を利用
        auth_url = request.user.endpoint
        user_name = request.user.username
        password = request.session.get('password')

        # Barbican接続
        conn = connection.Connection(
            auth_url=auth_url,
            username=user_name,
            password=password,
            project_name=request.user.project_name,
            user_domain_name='default',
            project_domain_name='default'
        )

        # 鍵一覧取得
        secrets = conn.key_manager.secrets()

        # 鍵データリスト作成
        secret_list = [{
            'name': secret.name,
            'id': secret.id,
            'status': secret.status
        } for secret in secrets]

        return render(request, 'barbican_ui/list_secrets.html', {'secrets': secret_list})
    except Exception as e:
        return render(request, 'barbican_ui/list_secrets.html', {'error': str(e)})
