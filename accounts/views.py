from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CustomUserCreationForm, ProfileForm
from .models import UserProfile
from orders.models import Order

def login_view(request):
    if request.method == 'POST':
        email = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('profile')
        else:
            return render(request, 'accounts/login.html', {'error': 'Неверный email или пароль'})
    return render(request, 'accounts/login.html')

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно! Добро пожаловать!')
            return redirect('profile')
        else:
            messages.error(request, 'Ошибка при регистрации. Проверьте введенные данные.')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})

@login_required
def profile(request):
    user = request.user
    try:
        user_profile = user.profile
    except UserProfile.DoesNotExist:
        user_profile = UserProfile(user=user)
        user_profile.save()

    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=user_profile, user=user)
        if form.is_valid():
            form.save()
            user.email = form.cleaned_data['email']
            user.save()
            messages.success(request, 'Профиль успешно обновлен!')
            return redirect('profile')
    else:
        form = ProfileForm(instance=user_profile, user=user)

    # Получаем заказы пользователя из orders.models.Order
    orders = Order.objects.filter(user=user).order_by('-created_at')

    # Добавляем статус на русском для отображения
    for order in orders:
        order.status_display = dict(Order.STATUS_CHOICES).get(order.status, order.status)

    return render(request, 'accounts/profile.html', {
        'form': form,
        'orders': orders,
    })

def logout_view(request):
    logout(request)
    return redirect('login')