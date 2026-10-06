from debug_toolbar.toolbar import debug_toolbar_urls
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from apps.custom_cake.views import index
from apps.orders.views import lk, order_history

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", index, name="index"),
    path("lk/", lk, name="lk"),
    path("lk-order/", order_history, name="lk-order"),
    path("auth/", include("apps.accounts.urls")),
    path("orders/", include("apps.orders.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += debug_toolbar_urls()
