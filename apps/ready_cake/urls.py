from django.urls import path

from . import views

urlpatterns = [
    path("", views.cake_list, name="cake_list"),
]
