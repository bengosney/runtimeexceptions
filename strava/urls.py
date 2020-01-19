from django.urls import path

from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('run/<int:runid>', views.run, name='run'),
    path('auth', views.auth, name='auth'),
    path('callback', views.auth_callback, name='auth_callback'),
    path('refresh/<int:stravaid>', views.refreshToken, name='refresh_token'),
]
