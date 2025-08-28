from django import forms
from .models import Branch , Restaurant

class BranchForm(forms.ModelForm):
    class Meta:
        model = Branch
        fields = ['name', 'address', 'qr_code']  
        labels = {
            'name': 'اسم الفرع',
            'address': 'عنوان الفرع',
            'qr_code': 'رمز الاستجابة السريع (QR)',
        }
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل اسم الفرع'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'أدخل عنوان الفرع'
            }),
            'qr_code': forms.ClearableFileInput(attrs={
                'class': 'form-control'
            }),
        }

class RestaurantForm(forms.ModelForm):
    class Meta:
        model = Restaurant
        fields = ['name', 'description']  
        labels = {
            'name': 'اسم المطعم',
            'description': 'الوصف',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ادخل اسم المطعم'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'ادخل وصف المطعم'}),
        }