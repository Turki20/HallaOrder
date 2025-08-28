from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from .models import Category, Product
from restaurants.models import Restaurant
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from users.decorators import restaurant_owner_required

def get_test_restaurant(resturant_id):
    """
    Helper function to get the first restaurant for testing purposes.
    Raises an error if no restaurants exist in the database.
    """
    restaurant = Restaurant.objects.get(pk = resturant_id)
    if not restaurant:
        raise Exception("DATABASE TEST ERROR: No restaurants found. Please create at least one restaurant in the Django Admin panel to proceed.")
    return restaurant

@restaurant_owner_required
def menu_view(request):
    """
    Main view to display the menu and handle ADDING new categories and products.
    """
    try:
        test_restaurant = get_test_restaurant(request.user.restaurants.id)
    except Exception as e:
        return HttpResponse(str(e))

    if request.method == 'POST':
        # --- Handle ADD Category ---
        if 'add_category' in request.POST:
            name = request.POST.get('name', '').strip()
            if name:
                Category.objects.create(restaurant=test_restaurant, name=name) # ماراح يضيف الفئة لصاحب المطعم راح يضيفها لاخر مطعم انضاف في الداتابيس
        
        # --- Handle ADD Product ---
        elif 'add_product' in request.POST:
            name = request.POST.get('name', '').strip()
            price = request.POST.get('price')
            category_id = request.POST.get('category')
            if name and price and category_id:
                try:
                    category = get_object_or_404(Category, id=category_id, restaurant=test_restaurant) # نفس مشكله الفئات
                    Product.objects.create(
                        category=category,
                        name=name,
                        price=Decimal(price),
                        description=request.POST.get('description', ''),
                        image=request.POST.get('image', '') or None
                    )
                except (ValueError, Category.DoesNotExist):
                    pass
        
        # --- Handle Toggle Product Availability (AJAX) ---
        elif 'toggle_product' in request.POST:
            product_id = request.POST.get('product_id')
            if product_id:
                try:
                    product = get_object_or_404(Product, id=product_id, category__restaurant=test_restaurant) # نفس مشكلة الفئات والمنتجات
                    product.available = not product.available
                    product.save()
                    return JsonResponse({'success': True, 'available': product.available})
                except Product.DoesNotExist:
                    return JsonResponse({'success': False})
        
        return redirect('menu:menu_view')

    # --- Display the Page (GET Request) ---
    categories = Category.objects.filter(restaurant=test_restaurant).prefetch_related('product_set') # بيرجع الفئات الخاصة بأول مطعم موجود في الداتابيس لازم تتعدل
    context = {'categories': categories}
    return render(request, 'menu/menu.html', context)

@restaurant_owner_required
def edit_category(request, category_id):
    """Edit category functionality"""
    try:
        test_restaurant = get_test_restaurant(request.user.restaurants.id)
        category = get_object_or_404(Category, id=category_id, restaurant=test_restaurant) # ----
        
        if request.method == 'POST':
            name = request.POST.get('name', '').strip()
            description = request.POST.get('description', '').strip()
            if name:
                category.name = name
                category.description = description or None
                category.save()
                return redirect('menu:menu_view')
        
        # Calculate statistics
        total_products = category.product_set.count()
        available_products = category.product_set.filter(available=True).count()
        unavailable_products = category.product_set.filter(available=False).count()
        
        context = {
            'category': category,
            'total_products': total_products,
            'available_products': available_products,
            'unavailable_products': unavailable_products,
        }
        return render(request, 'menu/edit_category.html', context)
    except Exception as e:
        return HttpResponse(str(e))

@restaurant_owner_required
def edit_product(request, product_id):
    """Edit product functionality"""
    try:
        test_restaurant = get_test_restaurant(request.user.restaurants.id)
        product = get_object_or_404(Product, id=product_id, category__restaurant=test_restaurant)
        categories = Category.objects.filter(restaurant=test_restaurant)
        
        if request.method == 'POST':
            name = request.POST.get('name', '').strip()
            price = request.POST.get('price')
            category_id = request.POST.get('category')
            description = request.POST.get('description', '').strip()
            image = request.FILES.get('image', None)
            available = request.POST.get('available', '1') == '1'
            
            if name and price and category_id:
                try:
                    category = get_object_or_404(Category, id=category_id, restaurant=test_restaurant)
                    product.name = name
                    product.price = Decimal(price)
                    product.category = category
                    product.description = description
                    if image != None:
                        product.image = image or None
                    product.available = available
                    product.save()
                    return redirect('menu:menu_view')
                except (ValueError, Category.DoesNotExist):
                    pass
        
        context = {'product': product, 'categories': categories}
        return render(request, 'menu/edit_product.html', context)
    except Exception as e:
        return HttpResponse(str(e))

@restaurant_owner_required
def delete_category(request, category_id):
    """Delete category functionality"""
    try:
        test_restaurant = get_test_restaurant(request.user.restaurants.id)
        category = get_object_or_404(Category, id=category_id, restaurant=test_restaurant)
        if request.method == 'POST':
            category.delete()
    except Exception:
        pass
    return redirect('menu:menu_view')

@restaurant_owner_required
def delete_product(request, product_id):
    """Delete product functionality"""
    try:
        test_restaurant = get_test_restaurant(request.user.restaurants.id)
        product = get_object_or_404(Product, id=product_id, category__restaurant=test_restaurant)
        if request.method == 'POST':
            product.delete()
    except Exception:
        pass
    return redirect('menu:menu_view')

@restaurant_owner_required
def toggle_product_availability(request, product_id):
    """AJAX endpoint to toggle product availability"""
    if request.method == 'POST':
        try:
            test_restaurant = get_test_restaurant(request.user.restaurants.id)
            product = get_object_or_404(Product, id=product_id, category__restaurant=test_restaurant)
            product.available = not product.available
            product.save()
            return JsonResponse({'success': True, 'available': product.available})
        except Exception:
            return JsonResponse({'success': False})
    return JsonResponse({'success': False})