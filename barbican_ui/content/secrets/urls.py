from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r'^$', views.IndexView.as_view(), name='index'),
    re_path(r'^create$', views.CreateSecretView.as_view(), name='create'),
    re_path(r'^auto_rotate$', views.AutoRotateSecretView.as_view(), name='auto_rotate'),
    re_path(r'^send_key_aws$', views.SendSecretAWSView.as_view(), name='send_key_aws'),
    re_path(r'^send_key_oracle$', views.SendSecretOracleView.as_view(), name='send_key_oracle'),
    re_path(r'^send_key_azure$', views.SendSecretAzureView.as_view(), name='send_key_azure'),
    re_path(r'^send_key_google$', views.SendSecretGoogleView.as_view(), name='send_key_google'),
    re_path(r'^select_google_connection$', views.SelectGoogleConnectionView.as_view(), name='select_google_connection'),
]