from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r'^$', views.IndexView.as_view(), name='index'),
    re_path(r'^create$', views.CreateSecretView.as_view(), name='create'),
    re_path(r'^send_key_oracle$', views.SendSecretOracleView.as_view(), name='send_key_oracle'),
]