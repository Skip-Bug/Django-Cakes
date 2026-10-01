from django.conf import settings


def jivosite(request):
    return {
        'JIVOSITE_WIDGET_ID': settings.JIVOSITE_WIDGET_ID,
    }