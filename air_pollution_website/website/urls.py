from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('home', views.home, name='home'),
    path('show', views.show, name='show'),
    path('about', views.about, name='about'),
    path('help', views.help, name='help'),
    path('download', views.download, name='download'),
    path('earth', views.earth, name='earth'),
]