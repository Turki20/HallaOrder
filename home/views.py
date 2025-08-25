from django.shortcuts import render, redirect
from django.http import HttpRequest
from django.contrib.auth.decorators import login_required
from restaurants.models import SubscriptionPlan, Restaurant
from menu.models import Product, Category
from django.contrib import messages
from django.db import transaction

# Create your views here.

# سوي ديكوريتر ان المستخدم يكون صاحب مطعم

def index_view(request:HttpRequest):
    
    return render(request, 'home/index.html')


@login_required(login_url='/users/sign_up/')
def subscriptionplan_view(request:HttpRequest):
    if request.method == 'POST':
        request.session['subscriptionplan_id'] = request.POST['subscriptionplan']
    
    subscriptionplan_data = request.session.get('subscriptionplan_id', None)
    subscription_plan_search = Restaurant.objects.filter(owner = request.user)
    if subscriptionplan_data is not None or len(subscription_plan_search) > 0:
        return redirect('home:create_restaurant_identity')
    
    subscriptionPlan = SubscriptionPlan.objects.all()
    return render(request, 'home/subscriptionplan.html', {'subscriptionPlan':subscriptionPlan})

@login_required(login_url='/users/sign_up/')
def create_restaurant_identity(request:HttpRequest):
    # لازم قبل يسوي انشاء للمطعم يختار الباقه
    subscriptionplan_data = request.session.get('subscriptionplan_id', None)
    if subscriptionplan_data is None:
        return redirect('home:subscriptionplan_view')
    
    return render(request, 'home/create_restaurant_identity.html')


@login_required(login_url='/users/sign_up/')
def restaurant_identity(request:HttpRequest):
    # لازم قبل يسوي انشاء للمطعم يختار الباقه
    subscriptionplan_data = request.session.get('subscriptionplan_id', None)
    if subscriptionplan_data is None:
        return redirect('home:subscriptionplan_view')
    
    # تحقق اذا كان المستخدم قد انشئ مطعم ولا باقي 
    # تحقق اذا كان المستخدم قد انشئ مطعم
    if Restaurant.objects.filter(owner=request.user).exists():
        messages.success(request, "تم انشاء هوية المطعم مسبقًا", 'alert-success')
        return redirect('home:create_restaurant_identity')
        
    if request.method == 'POST':
        restaurant_name = request.POST['restaurant_name']
        restaurant_desc = request.POST['restaurant_desc']
        restaurant_logo = request.FILES['restaurant_logo']
        primary_color = request.POST['primary_color']
        secondary_color = request.POST['secondary_color']
        
        if not restaurant_name or not restaurant_desc or not restaurant_logo or not primary_color:
            messages.error(request, "الرجاء تعبئة جميع الحقول المطلوبة", 'alert-danger')
            return render(request, 'home/restaurant_identity.html')
        
        restaurant = Restaurant(
            name = restaurant_name,
            description = restaurant_desc,
            owner = request.user,
            subscription_plan = SubscriptionPlan.objects.get(pk = subscriptionplan_data),
            slug = restaurant_name
        )
        
        restaurant.save()
        
        messages.success(request, "تم إنشاء هوية المطعم بنجاح", 'alert-success')
        return redirect('home:create_restaurant_identity')
            
    return render(request, 'home/restaurant_identity.html', {})

@login_required(login_url='/users/sign_up/')
def add_food_plate(request:HttpRequest):
    # تحقق يجب ان ينشئ المطعم اولا
    try:
        request.user.restaurants
    except:
        messages.error(request, "يجب انشاء هوية المطعم اولا", 'alert-danger')
        return redirect('home:create_restaurant_identity')
    
    if len(request.user.restaurants.category_set.all()) > 0:
        messages.success(request, "تم اضافة طبق مسبقًا", 'alert-success')
        return redirect('home:create_restaurant_identity')
    
    if request.method == "POST":
        category_name = request.POST.get("category_name", "").strip()
        category_desc = request.POST.get("category_desc", "").strip()
        dish_name = request.POST.get("dish_name", "").strip()
        dish_desc = request.POST.get("dish_desc", "").strip()
        dish_price = request.POST.get("dish_price", "").strip()
        dish_image = request.FILES.get("dish_image", None)

        # تحقق أساسي من المدخلات
        if not category_name:
            messages.error(request, "اسم الفئة مطلوب")
            return redirect('home:add_food_plate')

        if not dish_name:
            messages.error(request, "اسم الطبق مطلوب")
            return redirect('home:add_food_plate')

        if not dish_price or not dish_price.replace(".", "", 1).isdigit():
            messages.error(request, "الرجاء إدخال سعر صالح")
            return redirect('home:add_food_plate')

        if dish_image:
            allowed_types = ["image/png", "image/jpeg", "image/webp", "image/svg+xml"]
            if dish_image.content_type not in allowed_types:
                messages.error(request, "نوع الصورة غير مسموح. الأنواع المسموحة: PNG, JPG, WEBP, SVG")
                return redirect('home:add_food_plate')

        with transaction.atomic():
            category = Category(
                restaurant = request.user.restaurants,
                name = category_name,
                description = category_desc
            )

            category.save()

            # إنشاء الطبق
            dish = Product.objects.create(
                name=dish_name,
                description=dish_desc,
                price=float(dish_price),
                image=dish_image,
                category=category,
            )

        messages.success(request, f"تم إضافة الطبق '{dish.name}' بنجاح")
        restaurant = Restaurant.objects.get(pk = request.user.restaurants.id)
        restaurant.is_active = True
        restaurant.save()
        return redirect('restaurants')


    return render(request, 'home/add_food_plate.html', {})