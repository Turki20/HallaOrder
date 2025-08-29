# menu/forms.py

from django import forms
from django.forms import inlineformset_factory, modelformset_factory
from .models import OptionGroup, Option, Meal, MealItem, Product

class OptionGroupCreateForm(forms.ModelForm):
    class Meta:
        model = OptionGroup; fields = ['name', 'is_required']
        widgets = {'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'مثال: الحجم، الإضافات'}), 'is_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),}
        labels = {'name': 'اسم المجموعة', 'is_required': 'إجباري',}

class OptionGroupEditForm(forms.ModelForm):
    class Meta:
        model = OptionGroup; fields = ['name', 'selection_type', 'is_required', 'min_selection', 'max_selection']
        widgets = {'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'مثال: الحجم، الإضافات'}), 'selection_type': forms.Select(attrs={'class': 'form-select'}), 'is_required': forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'}), 'min_selection': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}), 'max_selection': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),}
        labels = {'name': 'اسم المجموعة', 'selection_type': 'نوع الاختيار', 'is_required': 'مجموعة إجبارية', 'min_selection': 'أقل عدد للاختيار', 'max_selection': 'أقصى عدد للاختيار',}

class OptionForm(forms.ModelForm):
    class Meta:
        model = Option; fields = ['name', 'price_adjustment', 'position']
        widgets = {'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'مثال: صغير، جبنة إضافية'}), 'price_adjustment': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}), 'position': forms.HiddenInput(),}

OptionFormSet = inlineformset_factory(OptionGroup, Option, form=OptionForm, fields=('name', 'price_adjustment', 'position'), extra=1, can_delete=True)

# --- NEW FORMS FOR PHASE 3 ---

class MealForm(forms.ModelForm):
    class Meta:
        model = Meal
        fields = ['name', 'description', 'price', 'image', 'available', 'option_groups']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'available': forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'}),
            # We will replace 'option_groups' with our custom widget in the template
        }

class MealItemForm(forms.ModelForm):
    class Meta:
        model = MealItem
        fields = ['product', 'quantity']
    
    def __init__(self, *args, **kwargs):
        # We need to pass the restaurant's products to the form's queryset
        restaurant = kwargs.pop('restaurant', None)
        super().__init__(*args, **kwargs)
        if restaurant:
            self.fields['product'].queryset = Product.objects.filter(category__restaurant=restaurant)
            self.fields['product'].widget.attrs.update({'class': 'form-select'})
            self.fields['quantity'].widget.attrs.update({'class': 'form-control', 'min': '1'})

MealItemFormSet = modelformset_factory(
    MealItem,
    form=MealItemForm,
    extra=1,
    can_delete=True,
)