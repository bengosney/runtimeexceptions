from django.contrib.auth.views import LogoutView
from django.urls import path

from strava import views

app_name = "strava"

urlpatterns = [
    path("", views.index, name="index"),
    path("activities", views.activities, name="activities"),
    path("activity/<int:activityid>", views.activity, name="activity"),
    path("img/<int:activityid>.png", views.activity_png, name="activity_png"),
    path("img/<int:activityid>.svg", views.activity_svg, name="activity_svg"),
    path("auth", views.auth, name="auth"),
    path("callback", views.auth_callback, name="auth_callback"),
    path("refresh/<int:strava_id>", views.refresh_token, name="refresh_token"),
    path("webhook", views.webhook, name="webhook"),
    path("logout", LogoutView.as_view(), name="logout"),
]
