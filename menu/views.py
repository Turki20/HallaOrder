# menu/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from restaurants.models import Restaurant
from .models import Category, Product, ProductImage, OptionGroup, Option, Meal, MealItem
from .forms import OptionGroupCreateForm, OptionGroupEditForm, OptionFormSet, MealForm, MealItemFormSet
from decimal import Decimal

def restaurant_owner_required(view_func):
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        try:
            restaurant = Restaurant.objects.get(owner=request.user)
            request.restaurant = restaurant
        except Restaurant.DoesNotExist:
            return HttpResponseForbidden("You are not associated with any restaurant.")
        except Restaurant.MultipleObjectsReturned:
            return HttpResponseBadRequest("Error: Multiple restaurants are associated with your account.")
        
        # Data isolation checks
        if 'category_id' in kwargs:
            obj = get_object_or_404(Category, pk=kwargs['category_id'])
            if obj.restaurant != request.restaurant: return HttpResponseForbidden("Access Denied")
        if 'product_id' in kwargs:
            obj = get_object_or_404(Product, pk=kwargs['product_id'])
            if obj.category.restaurant != request.restaurant: return HttpResponseForbidden("Access Denied")
        if 'image_id' in kwargs:
            obj = get_object_or_404(ProductImage, pk=kwargs['image_id'])
            if obj.product.category.restaurant != request.restaurant: return HttpResponseForbidden("Access Denied")
        if 'group_id' in kwargs:
            obj = get_object_or_404(OptionGroup, pk=kwargs['group_id'])
            if obj.restaurant != request.restaurant: return HttpResponseForbidden("Access Denied")
        if 'meal_id' in kwargs:
            obj = get_object_or_404(Meal, pk=kwargs['meal_id'])
            if obj.restaurant != request.restaurant: return HttpResponseForbidden("Access Denied")
            
        return view_func(request, *args, **kwargs)
    return _wrapped_view

@restaurant_owner_required
def menu_view(request):
    restaurant = request.restaurant
    if request.method == 'POST':
        if 'add_category' in request.POST:
            name = request.POST.get('name', '').strip()
            if name: Category.objects.create(restaurant=restaurant, name=name)
        elif 'add_product' in request.POST:
            name = request.POST.get('name', '').strip()
            price = request.POST.get('price')
            category_id = request.POST.get('category')
            if name and price and category_id:
                try:
                    category = get_object_or_404(Category, id=category_id, restaurant=restaurant)
                    new_product = Product.objects.create(category=category, name=name, price=Decimal(price), description=request.POST.get('description', ''))
                    return redirect('menu:edit_product', product_id=new_product.id)
                except (ValueError, Category.DoesNotExist): pass
        elif 'add_option_group' in request.POST:
            form = OptionGroupCreateForm(request.POST)
            if form.is_valid():
                group = form.save(commit=False); group.restaurant = restaurant; group.selection_type = 'SINGLE'; group.save()
        elif 'add_addon_group' in request.POST:
            form = OptionGroupCreateForm(request.POST)
            if form.is_valid():
                group = form.save(commit=False); group.restaurant = restaurant; group.selection_type = 'MULTIPLE'; group.save()
        return redirect('menu:menu_view')
    categories = Category.objects.filter(restaurant=restaurant).prefetch_related('products__images')
    all_option_groups = OptionGroup.objects.filter(restaurant=restaurant).prefetch_related('options')
    context = {
        'categories': categories,
        'option_groups': all_option_groups.filter(selection_type='SINGLE'),
        'addon_groups': all_option_groups.filter(selection_type='MULTIPLE'),
        'option_group_create_form': OptionGroupCreateForm(),
    }
    return render(request, 'menu/menu.html', context)

@restaurant_owner_required
def edit_category(request, category_id):
    category = get_object_or_404(Category, id=category_id, restaurant=request.restaurant)
    if request.method == 'POST':
        category.name = request.POST.get('name', '').strip()
        category.description = request.POST.get('description', '').strip()
        category.save()
        return redirect('menu:menu_view')
    total_products = category.products.count()
    available_products = category.products.filter(available=True).count()
    context = {'category': category, 'total_products': total_products, 'available_products': available_products, 'unavailable_products': total_products - available_products,}
    return render(request, 'menu/edit_category.html', context)

@restaurant_owner_required
def delete_category(request, category_id):
    category = get_object_or_404(Category, id=category_id, restaurant=request.restaurant)
    if request.method == 'POST': category.delete()
    return redirect('menu:menu_view')

@restaurant_owner_required
def edit_product(request, product_id):
    restaurant = request.restaurant
    product = get_object_or_404(Product, id=product_id, category__restaurant=restaurant)
    categories = Category.objects.filter(restaurant=restaurant)
    available_option_groups = OptionGroup.objects.filter(restaurant=restaurant)
    if request.method == 'POST':
        product.name = request.POST.get('name', '').strip()
        product.price = Decimal(request.POST.get('price'))
        product.category = get_object_or_404(Category, id=request.POST.get('category'), restaurant=restaurant)
        product.description = request.POST.get('description', '').strip()
        product.available = request.POST.get('available', '1') == '1'
        product.save()
        product.option_groups.set(request.POST.getlist('option_groups'))
        for image_file in request.FILES.getlist('images'):
            ProductImage.objects.create(product=product, image=image_file)
        return redirect('menu:edit_product', product_id=product.id)
    context = {'product': product, 'categories': categories, 'product_images': product.images.all(), 'available_option_groups': available_option_groups,}
    return render(request, 'menu/edit_product.html', context)

@restaurant_owner_required
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id, category__restaurant=request.restaurant)
    if request.method == 'POST': product.delete()
    return redirect('menu:menu_view')

@require_POST
@restaurant_owner_required
def toggle_product_availability(request, product_id):
    product = get_object_or_404(Product, id=product_id, category__restaurant=request.restaurant)
    product.available = not product.available
    product.save()
    return JsonResponse({'success': True, 'available': product.available})

@require_POST
@restaurant_owner_required
def set_cover_image(request, image_id):
    image = get_object_or_404(ProductImage, pk=image_id)
    image.is_cover = True
    image.save()
    return JsonResponse({'success': True})

@require_POST
@restaurant_owner_required
def delete_product_image(request, image_id):
    image = get_object_or_404(ProductImage, pk=image_id)
    image.delete()
    return JsonResponse({'success': True})

@restaurant_owner_required
def edit_option_group(request, group_id=None):
    restaurant = request.restaurant
    instance = get_object_or_404(OptionGroup, pk=group_id, restaurant=restaurant)
    form = OptionGroupEditForm(request.POST or None, instance=instance)
    formset = OptionFormSet(request.POST or None, instance=instance, prefix='options')
    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        return redirect('menu:menu_view')
    context = {'form': form, 'formset': formset, 'instance': instance}
    return render(request, 'menu/edit_option_group.html', context)

@require_POST
@restaurant_owner_required
def delete_option_group(request, group_id):
    group = get_object_or_404(OptionGroup, pk=group_id, restaurant=request.restaurant)
    group.delete()
    return redirect('menu:menu_view')

@restaurant_owner_required
def meal_management(request):
    restaurant = request.restaurant
    # --- THIS IS THE CORRECTED LINE ---
    # We prefetch the actual 'images' relationship on the product,
    # which allows the 'cover_image' property to work efficiently without extra queries.
    meals = Meal.objects.filter(restaurant=restaurant).prefetch_related('items__product__images')
    context = {'meals': meals}
    return render(request, 'menu/meal_management.html', context)

@restaurant_owner_required
def create_or_edit_meal(request, meal_id=None):
    restaurant = request.restaurant
    instance = None
    if meal_id:
        instance = get_object_or_404(Meal, pk=meal_id, restaurant=restaurant)
    form = MealForm(request.POST or None, request.FILES or None, instance=instance)
    queryset = MealItem.objects.filter(meal=instance) if instance else MealItem.objects.none()
    formset = MealItemFormSet(request.POST or None, queryset=queryset, form_kwargs={'restaurant': restaurant}, prefix='items')
    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        meal = form.save(commit=False)
        meal.restaurant = restaurant
        meal.save()
        form.save_m2m()
        items = formset.save(commit=False)
        for item in items:
            item.meal = meal
            item.save()
        for deleted_form in formset.deleted_forms:
            if deleted_form.instance.pk: deleted_form.instance.delete()
        return redirect('menu:meal_management')
    available_option_groups = OptionGroup.objects.filter(restaurant=restaurant)
    context = {'form': form, 'formset': formset, 'instance': instance, 'available_option_groups': available_option_groups}
    return render(request, 'menu/meal_form.html', context)

@require_POST
@restaurant_owner_required
def delete_meal(request, meal_id):
    meal = get_object_or_404(Meal, pk=meal_id, restaurant=request.restaurant)
    meal.delete()
    return redirect('menu:meal_management')