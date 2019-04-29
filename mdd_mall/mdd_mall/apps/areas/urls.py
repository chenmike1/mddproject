from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^areas/$', views.ProvinceAreasView.as_view()),
    url(r'^areas/(?P<pk>[1-9]\d+)/$', views.SubAreasView.as_view()),
]
