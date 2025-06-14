from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from catalog.models import Product
from django.views.decorators.http import require_POST

from .models import Favorite

@login_required
def favorites_view(request):
    favorites = (Favorite.objects
                 .filter(user=request.user).select_related('product'))
    return render(request, 'favorites/favorites.html',
                  {'favorites': favorites})

@login_required
@require_POST
def toggle_favorite(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    favorite, created = Favorite.objects.get_or_create(user=request.user,
                                                       product=product)
    if not created:
        favorite.delete()
        is_favorite = False
    else:
        is_favorite = True

    return JsonResponse({'success': True, 'is_favorite': is_favorite,
                         'product_id': product_id})