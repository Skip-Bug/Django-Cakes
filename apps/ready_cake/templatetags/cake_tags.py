from django import template

from apps.ready_cake.models import Cake

register = template.Library()


@register.inclusion_tag("ready_cake/_catalog.html")
def show_catalog():
    return {
        "cakes": Cake.objects.filter(is_active=True).prefetch_related(
            "restricted_parts"
        )
    }
