from django.contrib import admin
from .models import CartItem

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'size', 'quantity')
    list_filter = ('product', 'size')
    search_fields = ('user__email', 'product__name')
