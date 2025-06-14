from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import CustomUser, UserProfile
from datetime import datetime
import re

CustomUser = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=100, required=True, label='Имя')
    last_name = forms.CharField(max_length=100, required=True, label='Фамилия')
    email = forms.EmailField(required=True, label='Email')

    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = user.email  # Используем email как username
        if commit:
            user.save()
            # Создаем профиль пользователя
            UserProfile.objects.update_or_create(
                user=user,
                defaults={
                    'first_name': self.cleaned_data['first_name'],
                    'gender': '',
                    'birth_date': None,
                    'city': '',
                    'phone': ''
                }
            )
        return user

class ProfileForm(forms.ModelForm):
    email = forms.EmailField(required=True, label='Email')
    first_name = forms.CharField(max_length=100, required=True, label='Имя')
    last_name = forms.CharField(max_length=100, required=True, label='Фамилия')

    class Meta:
        model = UserProfile
        fields = ['first_name', 'gender', 'birth_date', 'city', 'phone']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['email'].initial = self.user.email
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name

    def save(self, *args, **kwargs):
        user_profile = super().save(*args, **kwargs)
        if self.user:
            self.user.email = self.cleaned_data['email']
            self.user.first_name = self.cleaned_data['first_name']
            self.user.last_name = self.cleaned_data['last_name']
            self.user.save()
        return user_profile