from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import TemplateView

from apps.custom_cake.views import index


@method_decorator(ensure_csrf_cookie, name="dispatch")
class CsrfTemplateView(TemplateView):
    """TemplateView, который гарантированно выставляет CSRF-куку."""


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", index, name="index"),
    path(
        "lk/",
        CsrfTemplateView.as_view(template_name="lk.html"),
        name="lk",
    ),
    path(
        "lk-order/",
        CsrfTemplateView.as_view(template_name="lk-order.html"),
        name="lk-order",
    ),
    path("auth/", include("apps.accounts.urls")),
    path("orders/", include("apps.orders.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
