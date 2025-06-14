from django import forms
from accounts.models import UserProfile

class CheckoutForm(forms.Form):
    name = forms.CharField(max_length=100, required=True, label="Имя")
    city = forms.CharField(max_length=100, required=True, label="Город", widget=forms.TextInput(attrs={'id': 'city-input'}))
    address_detail = forms.CharField(max_length=255, required=True, label="Детальный адрес", widget=forms.TextInput(attrs={'id': 'address-detail-input'}))
    email = forms.EmailField(required=True, label="E-mail")
    phone = forms.CharField(max_length=20, required=True, label="Телефон", help_text="Введите номер в формате +79991234567")
    delivery_method = forms.ChoiceField(
        choices=[('post', 'Почта России'), ('courier', 'Курьер')],
        widget=forms.RadioSelect,
        required=True,
        label="Способ доставки"
    )

    def clean_phone(self):
        phone = self.cleaned_data['phone']
        if not phone.startswith('+'):
            raise forms.ValidationError("Номер телефона должен начинаться с '+' (например, +79991234567).")
        return phone


    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        profile = UserProfile.objects.filter(user=user).first()
        if profile:
            self.fields['name'].initial = profile.first_name
            self.fields['city'].initial = profile.city
            self.fields['email'].initial = user.email
            self.fields['phone'].initial = profile.phone

    def save_to_profile(self, user):
        profile, created = UserProfile.objects.get_or_create(user=user)
        profile.first_name = self.cleaned_data['name']
        profile.city = self.cleaned_data['city']
        profile.phone = self.cleaned_data['phone']
        profile.save()
        user.email = self.cleaned_data['email']
        user.save()