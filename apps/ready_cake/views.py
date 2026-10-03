from django.shortcuts import render 
from .models import Cake

def cake_list(request):
    cakes = Cake.objects.filter()
    return render(request, 'goods/index.html', {'cakes': cakes})
