from django.urls import path
from . import views

urlpatterns = [
    path('', views.favorites_view, name='favorites'),
    path('toggle/<int:product_id>/', views.toggle_favorite, name='toggle_favorite'),
]