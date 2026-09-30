from django.contrib import admin
from django.urls import path, include
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import TemplateView


@method_decorator(ensure_csrf_cookie, name="dispatch")
class CsrfTemplateView(TemplateView):
    """TemplateView, который гарантированно выставляет CSRF-куку."""


urlpatterns = [
    path("admin/", admin.site.urls),

    path(
        "",
        CsrfTemplateView.as_view(template_name="index.html"),
        name="index",
    ),
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
]
