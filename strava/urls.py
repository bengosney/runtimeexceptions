from django.urls import path

from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('activity/<int:activityid>', views.activity, name='activity'),
    path('img/<int:activityid>.png', views.activityImage, name='activity_image'),
    path('auth', views.auth, name='auth'),
    path('callback', views.auth_callback, name='auth_callback'),
    path('refresh/<int:stravaid>', views.refreshToken, name='refresh_token'),
]
