# Django
from django.urls import path

# First Party
from strava import views

app_name = "strava"

urlpatterns = [
    path("", views.activities, name="activities"),
    path("activity/<int:activityid>", views.activity, name="activity"),
    path("img/<int:activityid>.png", views.activity_png, name="activity_png"),
    path("img/<int:activityid>.svg", views.activity_svg, name="activity_svg"),
    path("auth", views.auth, name="auth"),
    path("login", views.login_page, name="login"),
    path("callback", views.auth_callback, name="auth_callback"),
    path("refresh/<int:stravaid>", views.refresh_token, name="refresh_token"),
]
