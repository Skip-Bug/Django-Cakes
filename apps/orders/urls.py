from django.urls import path

from .views import order_create, payment_page, payment_process, ready_order_create

app_name = "orders"

urlpatterns = [
    path("", order_create, name="create"),
    path("ready/", ready_order_create, name="ready-create"),
    path("pay/<str:number>/<str:token>/", payment_page, name="pay"),
    path("pay/<str:number>/<str:token>/submit/", payment_process, name="pay-submit"),
]
