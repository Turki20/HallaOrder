from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .models import Category, Product
from restaurants.models import Restaurant # Make sure to import your Restaurant model

def get_test_restaurant():
    """
    Helper function to get the first restaurant for testing purposes.
    Raises an error if no restaurants exist in the database.
    """
    restaurant = Restaurant.objects.first()
    if not restaurant:
        # This error is a safeguard. You must create a restaurant in the admin panel.
        raise Exception("DATABASE TEST ERROR: No restaurants found. Please create at least one restaurant in the Django Admin panel to proceed.")
    return restaurant

def menu_view(request):
    """
    Main view to display the menu and handle ADDING new categories and products.
    """
    try:
        test_restaurant = get_test_restaurant()
    except Exception as e:
        return HttpResponse(str(e)) # Show the error message if no restaurant exists

    if request.method == 'POST':
        # --- Handle ADD Category ---
        if 'add_category' in request.POST:
            name = request.POST.get('name', '').strip()
            if name:
                Category.objects.create(restaurant=test_restaurant, name=name)
        
        # --- Handle ADD Product ---
        elif 'add_product' in request.POST:
            name = request.POST.get('name', '').strip()
            price = request.POST.get('price')
            category_id = request.POST.get('category')
            if name and price and category_id:
                category = get_object_or_404(Category, id=category_id, restaurant=test_restaurant)
                Product.objects.create(
                    category=category,
                    name=name,
                    price=price,
                    description=request.POST.get('description', ''),
                    image=request.POST.get('image', '')
                )
        return redirect('menu:menu')

    # --- Display the Page (GET Request) ---
    categories = Category.objects.filter(restaurant=test_restaurant).prefetch_related('product_set')
    context = {'categories': categories}
    return render(request, 'menu/menu.html', context)

# --- EDIT Functions (Placeholders) ---
def edit_category(request, category_id):
    # This is a placeholder. A full implementation would require a separate form/page.
    print(f"Placeholder: Would edit category with ID {category_id}")
    return redirect('menu:menu')

def edit_product(request, product_id):
    # Placeholder for edit functionality.
    print(f"Placeholder: Would edit product with ID {product_id}")
    return redirect('menu:menu')

# --- DELETE Functions (Simple & Functional) ---
def delete_category(request, category_id):
    test_restaurant = get_test_restaurant()
    category = get_object_or_404(Category, id=category_id, restaurant=test_restaurant)
    if request.method == 'POST':
        category.delete()
    return redirect('menu:menu')

def delete_product(request, product_id):
    test_restaurant = get_test_restaurant()
    product = get_object_or_404(Product, id=product_id, category__restaurant=test_restaurant)
    if request.method == 'POST':
        product.delete()
    return redirect('menu:menu')