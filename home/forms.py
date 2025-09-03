from django import forms
from restaurants.models import RestaurantVerification

class RestaurantVerificationForm(forms.ModelForm):
    class Meta:
        model = RestaurantVerification
        fields = ["category", "phone", "email", "commercial_registration", "vat_number", "iban"]
        widgets = {
            "category": forms.TextInput(attrs={"class": "form-control", "placeholder": "مثال: مطعم، كوفي"}),
            "phone": forms.TextInput(attrs={"class": "form-control", "placeholder": "05xxxxxxxx"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "example@email.com"}),
            "commercial_registration": forms.TextInput(attrs={"class": "form-control", "placeholder": "رقم السجل التجاري"}),
            "vat_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "رقم ضريبة القيمة المضافة"}),
            "iban": forms.TextInput(attrs={"class": "form-control", "placeholder": "SAxx xxxx xxxx xxxx"}),
        }
