from django.urls import path

from . import views

urlpatterns = [
    path("request-code/", views.request_code, name="request_code"),
    path("verify-code/", views.verify_code, name="verify_code"),
    path("logout/", views.logout_view, name="logout"),
    path("me/", views.me, name="me"),
]