from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from openstack import connection
from openstack_dashboard.api import keystone
import json

@csrf_exempt
def create_aes_key(request):
    """Creates a 256-bit AES key using Horizon session credentials."""
    if request.method == 'POST':
        try:
            # Horizonセッションから認証情報を取得
            auth_url = keystone.get_auth_url()
            user_token = request.user.token.id
            project_id = request.user.tenant_id

            # ユーザ入力を取得
            data = json.loads(request.body)
            key_name = data.get('name', 'AES-256-Key')  # デフォルト値を設定
            key_description = data.get('description', 'No description provided.')

            # OpenStack接続を初期化
            conn = connection.Connection(
                auth_url=auth_url,
                token=user_token,
                project_id=project_id
            )
            barbican = conn.key_manager

            # 256ビット鍵データを生成
            key_data = b'\x00' * 32

            # 鍵をBarbicanに作成
            secret = barbican.secrets.create(
                name=key_name,
                payload=key_data,
                payload_content_type='application/octet-stream',
                algorithm='AES',
                bit_length=256,
                mode='cbc',
                description=key_description
            )
            secret.store()

            return JsonResponse({"message": f"AES key '{key_name}' created successfully!"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Invalid request method."}, status=405)
