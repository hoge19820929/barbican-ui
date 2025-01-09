from django.urls import re_path
from . import views

app_name = 'barbican_ui'

urlpatterns = [
    re_path(r'^$', views.create_key, name='index'),
    re_path(r'^create-key/$', views.create_key, name='create_key'),
    re_path(r'^list-secrets/$', views.list_secrets, name='list_secrets'),
]
