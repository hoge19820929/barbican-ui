from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r'^$', views.IndexView.as_view(), name='index'),
    re_path(r'^auto_rotate$', views.AutoRotateSecretView.as_view(), name='auto_rotate'),
    re_path(r'^set_cred$', views.SetCredentialsView.as_view(), name='set_cred'),
    # re_path(r'^create$', views.CreateSecretView.as_view(), name='create'),
]