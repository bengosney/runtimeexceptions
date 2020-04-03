# Django
from django.urls import path

# Locals
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('activity/<int:activityid>', views.activity, name='activity'),
    path('img/<int:activityid>.png', views.activity_image, name='activity_image'),
    path('auth', views.auth, name='auth'),
    path('login', views.login_page, name='login'),
    path('callback', views.auth_callback, name='auth_callback'),
    path('refresh/<int:stravaid>', views.refresh_token, name='refresh_token'),
]
