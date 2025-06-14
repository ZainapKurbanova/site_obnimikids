import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from catalog.models import Product, Size
from orders.models import Order, OrderItem
from .models import CartItem
import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules
from mlxtend.preprocessing import TransactionEncoder
import random

@login_required
def cart_view(request):
    items = CartItem.objects.filter(user=request.user).select_related('product', 'size')
    total_price = sum(item.get_total_price() for item in items)
    return render(request, 'cart/cart.html', {'cart_items': items, 'total_price': total_price})


@login_required
def cart_view(request):
    cart_items = CartItem.objects.filter(user=request.user).select_related('product', 'size')
    total_price = sum(item.get_total_price() for item in cart_items)
    cart_product_ids = [item.product.id for item in cart_items]
    orders = Order.objects.all().prefetch_related('items__product')
    transactions = []
    for order in orders:
        transaction = [item.product.id for item in order.items.all()]
        if transaction:
            transactions.append(transaction)
    suggested_products = []
    if transactions and cart_product_ids:
        try:
            te = TransactionEncoder()
            te_ary = te.fit(transactions).transform(transactions)
            df = pd.DataFrame(te_ary, columns=te.columns_)

            frequent_itemsets = apriori(df, min_support=0.001, use_colnames=True)
            if not frequent_itemsets.empty:
                rules = association_rules(frequent_itemsets, metric="confidence",
                                          min_threshold=0.05)

                recommended_product_ids = set()
                for product_id in cart_product_ids:
                    relevant_rules = rules[rules['antecedents'].apply(lambda x: product_id in x)]
                    if not relevant_rules.empty:
                        for consequents in relevant_rules['consequents']:
                            for consequent in consequents:
                                if consequent not in cart_product_ids:
                                    recommended_product_ids.add(consequent)
                print("Рекомендованные ID товаров:", recommended_product_ids)  # Отладка

                suggested_products = Product.objects.filter(id__in=recommended_product_ids)
        except Exception as e:
            print("Ошибка при генерации рекомендаций:", e)

    if suggested_products or cart_items:
        target_count = 5
        if suggested_products:
            suggested_products = list(suggested_products)[:target_count]  # Ограничиваем до 5
        else:
            suggested_products = []

        if len(suggested_products) < target_count and cart_items:
            categories = set(item.product.category for item in cart_items if item.product.category)
            if categories:
                all_products_in_categories = Product.objects.filter(category__in=categories).exclude(id__in=cart_product_ids)
                if all_products_in_categories.exists():
                    remaining_count = target_count - len(suggested_products)
                    random_products = random.sample(list(all_products_in_categories), min(remaining_count, all_products_in_categories.count()))
                    suggested_products.extend(random_products)
        suggested_products = suggested_products[:target_count]
    if not suggested_products and cart_items:
        categories = set(item.product.category for item in cart_items if item.product.category)
        if categories:
            suggested_products = list(Product.objects.filter(category__in=categories).exclude(id__in=cart_product_ids).order_by('?')[:target_count])
    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'suggested_products': suggested_products,
    }
    return render(request, 'cart/cart.html', context)
@login_required
@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    size_name = request.POST.get('size')
    color = request.POST.get('color')
    quantity = int(request.POST.get('quantity', 1))

    if not size_name:
        return JsonResponse({'success': False, 'error': 'Пожалуйста, выберите размер.'}, status=400)

    size = get_object_or_404(Size, name=size_name)

    cart_item, created = CartItem.objects.get_or_create(
        user=request.user,
        product=product,
        size=size,
        defaults={'quantity': quantity}
    )

    if not created:
        cart_item.quantity += quantity
        cart_item.save()

    return JsonResponse({
        'success': True,
        'message': f'Товар {product.name} добавлен в корзину!',
        'product_id': product_id
    })

@login_required
@require_POST
def update_quantity(request, item_id):
    try:
        item = CartItem.objects.get(id=item_id, user=request.user)
        data = json.loads(request.body)
        new_quantity = data.get('quantity', item.quantity)
        print(f"Обновление item_id: {item_id}, new_quantity: {new_quantity}")

        if new_quantity < 1:
            return JsonResponse({'success': False, 'error': 'Количество не может быть меньше 1'}, status=400)

        item.quantity = new_quantity
        item.save()

        total_price = sum(item.get_total_price() for item in CartItem.objects.filter(user=request.user))
        print(f"Total price: {total_price}, Item count: {CartItem.objects.filter(user=request.user).count()}")
        return JsonResponse({
            'success': True,
            'item_total_price': item.get_total_price(),
            'total_price': total_price,
            'item_count': CartItem.objects.filter(user=request.user).count()
        })
    except CartItem.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Товар не найден'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@require_POST
def remove_item(request, item_id):
    try:
        item = CartItem.objects.get(id=item_id, user=request.user)
        print(f"Удаление item_id: {item_id}")
        item.delete()
        total_price = sum(item.get_total_price() for item in CartItem.objects.filter(user=request.user))
        print(f"Total price: {total_price}, Item count: {CartItem.objects.filter(user=request.user).count()}")
        return JsonResponse({
            'success': True,
            'total_price': total_price,
            'item_count': CartItem.objects.filter(user=request.user).count()
        })
    except CartItem.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Товар не найден'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

