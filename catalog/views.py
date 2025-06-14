from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from catalog.models import Product, Review
from favorites.models import Favorite
from orders.models import Order, OrderItem
from django.db.models import Q

def catalog(request):
    category = request.GET.get('category', None)
    search_query = request.GET.get('search', None)

    products = Product.objects.all()

    if category:
        products = products.filter(category=category)

    if search_query:
        products = products.filter(Q(name__icontains=search_query))

    categories = Product.CATEGORY_CHOICES

    return render(request, 'catalog/catalog.html', {
        'products': products,
        'categories': categories,
        'selected_category': category,
        'search_query': search_query
    })

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    is_favorite = False
    can_review = False
    has_reviewed = False

    if request.user.is_authenticated:
        is_favorite = Favorite.objects.filter(user=request.user, product=product).exists()
        has_purchased = OrderItem.objects.filter(
            order__user=request.user,
            product=product,
            order__status__in=['delivered', 'shipped']
        ).exists()
        has_reviewed = Review.objects.filter(user=request.user, product=product).exists()
        can_review = has_purchased and not has_reviewed

    if request.method == 'POST':
        if 'add_to_cart' in request.POST:
            size = request.POST.get('size')
            quantity = int(request.POST.get('quantity', 1))
            messages.success(request, f'Добавлено {quantity} шт. {product.name} (размер {size}) в корзину!')
            return redirect('product_detail', product_id=product_id)
        elif 'add_review' in request.POST and request.user.is_authenticated and can_review:
            rating = int(request.POST.get('rating', 0))
            comment = request.POST.get('comment', '').strip()
            if rating < 1 or rating > 5:
                messages.error(request, 'Пожалуйста, выберите рейтинг от 1 до 5 звёзд.')
            elif not comment:
                messages.error(request, 'Пожалуйста, напишите отзыв.')
            else:
                Review.objects.create(
                    product=product,
                    user=request.user,
                    rating=rating,
                    comment=comment
                )
                product.update_average_rating()
                messages.success(request, 'Ваш отзыв успешно добавлен!')
                return redirect('product_detail', product_id=product_id)

    return render(request, 'catalog/product_detail.html', {
        'product': product,
        'is_favorite': is_favorite,
        'can_review': can_review,
        'has_reviewed': has_reviewed,
    })