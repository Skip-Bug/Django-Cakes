from .models import Cake


def ready_cakes(request):
    return {
        "cakes": Cake.objects.all(),
    }
