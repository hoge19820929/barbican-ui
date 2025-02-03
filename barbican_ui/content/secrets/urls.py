from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r'^$', views.IndexView.as_view(), name='index'),
    re_path(r'^create$', views.CreateSecretView.as_view(), name='create'),
]