from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^qq/authorization/$', views.QQURLView.as_view()),
    url(r'^oauth_callback/$', views.QQUserView.as_view()),
]
