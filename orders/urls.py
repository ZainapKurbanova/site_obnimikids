from django.urls import path
from . import views

urlpatterns = [
    path('checkout/', views.checkout_view, name='checkout'),
    path('process-order/', views.process_order, name='process_order'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/user/<str:username>/orders/', views.admin_user_orders, name='admin_user_orders'),
    path('success/<int:order_id>/', views.order_success, name='order_success'),
]