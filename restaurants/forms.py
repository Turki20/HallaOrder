from django import forms
from .models import Branch , Restaurant

class BranchForm(forms.ModelForm):
    class Meta:
        model = Branch
        fields = ['restaurant', 'name', 'address', 'qr_code']  
        labels = {
            'restaurant': 'المطعم',
            'name': 'اسم الفرع',
            'address': 'عنوان الفرع',
            'qr_code': 'رمز الاستجابة السريع (QR)',
        }
        widgets = {
            'restaurant': forms.Select(attrs={
                'class': 'form-control',
            }),
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
        fields = ['name', 'description', 'owner']  
        labels = {
            'name': 'اسم المطعم',
            'description': 'الوصف',
            'owner': 'المالك',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ادخل اسم المطعم'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'ادخل وصف المطعم'}),
            'owner': forms.Select(attrs={'class': 'form-control'}),
        }