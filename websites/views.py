from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from menu.models import Product
from .models import Website


# =============================
# أدوات مساعدة للسلة (Session)
# =============================

def _cart_key(website_id: int) -> str:
    # مفتاح السلة في الـ Session متعلق بكل موقع على حدة
    return f"cart_{website_id}"


def _get_cart(request, website):
    # جلب السلة الحالية من الـ Session (قائمة عناصر)
    return request.session.get(_cart_key(website.id), [])


def _set_cart(request, website, value):
    # حفظ السلة في الـ Session ووضع modified=True لضمان الكتابة
    request.session[_cart_key(website.id)] = value
    request.session.modified = True


def _base_ctx(request, website, **extra):
    # سياق أساسي تُضاف له المتغيرات المشتركة لكل الصفحات العامة
    cart = _get_cart(request, website)
    cart_count = sum(int(item.get("qty", 1) or 1) for item in cart)
    ctx = {
        "website": website,
        "cart": cart,
        "cart_count": cart_count,
        # يوفر آخر رقم طلب لتمكين رابط العودة إلى الفاتورة
        "last_order_id": request.session.get("last_order_id"),
    }
    ctx.update(extra)
    return ctx


# =============================
# صفحات العرض العامة
# =============================

def menu_view(request, slug):
    # جلب الموقع والمطعم المرتبط به ثم تجميع كل المنتجات من التصنيفات
    website = get_object_or_404(Website.objects.select_related("restaurant"), slug=slug)
    categories = website.restaurant.category_set.all()
    products = []
    # for category in categories:
    #     for p in category.product_set.all():
    #         products.append(p)

    return render(
        request,
        "websites/menu.html",
        _base_ctx(request, website, products=products, current_tab="menu", categories=categories),
    )


def product_detail(request, slug, product_id):
    # صفحة تفاصيل منتج واحد
    website = get_object_or_404(Website.objects.select_related("restaurant"), slug=slug)
    product = Product.objects.get(id=product_id)
    return render(
        request,
        "websites/product_detail.html",
        _base_ctx(request, website, p=product, current_tab="menu"),
    )


# =============================
# عمليات السلة
# =============================
@require_POST
def add_to_cart(request, slug, product_id):
    # جلب الموقع والمنتج
    website = get_object_or_404(Website, slug=slug)
    p = get_object_or_404(Product, id=product_id)
    cart = _get_cart(request, website)

    # الكمية
    qty = request.POST.get("qty", "1")
    try:
        qty = max(int(qty), 1)
    except (TypeError, ValueError):
        qty = 1

    # السعر الأساسي
    final_price = float(p.price)

    # الخيارات
    selected_options = {}
    for group in p.option_groups.all():
        if group.selection_type == "SINGLE":
            value = request.POST.get(group.name, "")
            if value:
                selected_options[group.name] = value
                # حساب تعديل السعر
                option_obj = group.options.filter(name=value).first()
                if option_obj and option_obj.price_adjustment:
                    final_price += float(option_obj.price_adjustment)

        elif group.selection_type == "MULTIPLE":
            values = request.POST.getlist(group.name)
            if values:
                selected_options[group.name] = values
                # حساب تعديل السعر لكل خيار
                for val in values:
                    option_obj = group.options.filter(name=val).first()
                    if option_obj and option_obj.price_adjustment:
                        final_price += float(option_obj.price_adjustment)

    # ضرب الكمية
    total_price = final_price * qty

    # إضافة المنتج للسلة
    item = {
        "id": p.id,
        "name": str(p.name),
        "base_price": float(p.price),
        "final_price": final_price,  # سعر المنتج مع الخيارات (لكل قطعة)
        "price": total_price,  # السعر النهائي × الكمية
        "qty": qty,
        "options": selected_options,
    }

    cart.append(item)
    _set_cart(request, website, cart)

    return redirect("websites:menu", slug=slug)

# @require_POST
# def add_to_cart(request, slug, product_id):
#     # إضافة منتج للسلة مع الكمية والخيارات (الحجم/الإضافات)
#     website = get_object_or_404(Website, slug=slug)
#     p = Product.objects.get(id=product_id)
#     cart = _get_cart(request, website)

#     qty = request.POST.get("qty", "1")
#     try:
#         qty = max(int(qty), 1)
#     except (TypeError, ValueError):
#         qty = 1

#     item = {
#         "id": p.id,
#         "name": str(p.name),
#         "price": str(p.price),
#         "qty": qty,
#         "size": request.POST.get("size", ""),
#         "addons": request.POST.getlist("addons"),
#     }
#     cart.append(item)
#     _set_cart(request, website, cart)

#     return redirect("websites:menu", slug=slug)


def cart_view(request, slug):
    # صفحة السلة: تُظهر العناصر والحسابات + حقول بيانات العميل
    website = get_object_or_404(Website, slug=slug)
    cart = _get_cart(request, website)
    meta = _get_cart_meta(request, website)

    # حساب الإجمالي والضريبة (15%)
    subtotal = sum((float(i.get("price", 0))) for i in cart)
    tax_rate = 1 #0.15
    tax = 0 #round(subtotal * tax_rate, 2)
    total = round(subtotal + tax, 2)

    return render(
        request,
        "websites/cart.html",
        _base_ctx(
            request,
            website,
            cart=cart,
            subtotal=subtotal,
            tax=tax,
            total=total,
            tax_rate=int(tax_rate * 100),
            meta=meta,
            current_tab="cart",
        ),
    )


@require_POST
def remove_from_cart(request, slug, index):
    # حذف عنصر من السلة حسب ترتيبه
    website = get_object_or_404(Website, slug=slug)
    cart = _get_cart(request, website)
    try:
        idx = int(index)
        if 0 <= idx < len(cart):
            cart.pop(idx)
            _set_cart(request, website, cart)
    except (TypeError, ValueError):
        pass
    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER")
    if next_url:
        return redirect(next_url)
    return redirect("websites:cart", slug=slug)


# صفحات المعاينة (للمالِك/المدير)
@login_required
def preview_by_pk(request, pk):
    website = get_object_or_404(Website.objects.select_related("restaurant"), pk=pk)
    return redirect("websites:public", slug=website.slug)


@login_required
def preview_my_site(request):
    # اختيار موقع مناسب للمستخدم الحالي للمعاينة
    qs = Website.objects.select_related("restaurant")
    website = None

    mgr = getattr(request.user, "restaurants", None)
    if mgr and hasattr(mgr, "all"):
        website = qs.filter(restaurant__in=mgr.all()).order_by("-id").first()

    if not website:
        website = (
            qs.filter(restaurant__owner=request.user).order_by("-id").first()
            or qs.filter(restaurant__user=request.user).order_by("-id").first()
        )
    if not website:
        website = qs.order_by("-id").first()
    if not website:
        return HttpResponse("لا يوجد موقع مرتبط بحسابك بعد.", status=404)
    return redirect("websites:public", slug=website.slug)


# =============================
# بيانات عميل السلة (Session)
# =============================

def _meta_key(website_id: int) -> str:
    # مفتاح بيانات العميل في الـ Session
    return f"cart_meta_{website_id}"


def _get_cart_meta(request, website):
    # قراءة بيانات العميل المحفوظة (اسم/جوال/ملاحظات)
    return request.session.get(_meta_key(website.id), {"name": "", "phone": "", "notes": "", 'email': ''})


def _set_cart_meta(request, website, value):
    # حفظ بيانات العميل في الـ Session
    request.session[_meta_key(website.id)] = value
    request.session.modified = True


@require_POST
def save_cart_meta(request, slug):
    # حفظ بيانات العميل ثم الانتقال مباشرة إلى الدفع (Stripe)
    website = get_object_or_404(Website, slug=slug)
    meta = _get_cart_meta(request, website)
    meta.update({
        "name": request.POST.get("name", "").strip(),
        "phone": request.POST.get("phone", "").strip(),
        "notes": request.POST.get("notes", "").strip(),
        "email": request.POST.get("email", "").strip(),
    })
    _set_cart_meta(request, website, meta)

    # حفظ السجل لاستخدامه في الإرجاع من صفحة الإلغاء
    request.session["last_cart_slug"] = slug
    request.session.modified = True

    # حساب إجمالي الفاتورة ثم إنشاء جلسة دفع سريعة
    cart = _get_cart(request, website)
    subtotal = sum((float(i.get("price", 0))) for i in cart)
    tax = round(subtotal * 1, 2)
    total = round(subtotal, 2)

    from django.urls import reverse
    from urllib.parse import urlencode
    params = urlencode({"amount": f"{total}", "currency": "sar", "slug": slug, "email": meta.get("email", "")})
    return redirect(f"{reverse('payments:quick_checkout')}?{params}")

@require_POST
def save_dinein_details(request):
    dine_data = {
        'order_method': 'dine_in',
        'dinein': {
            'number_of_people': request.POST.get('number_of_people'),
            'branch_id': request.POST.get('branch_id'),
            'reservation_time': request.POST.get('reservation_time', ''),
            'special_requests': request.POST.get('special_requests', ''),
        }
    }
    request.session['order_data'] = dine_data
    return redirect(request.META.get('HTTP_REFERER', '/'))  # أو إلى صفحة المراجعة


@require_POST
def save_pickup_details(request):
    pickup_data = {
        'order_method': 'pickup',
        'pickup': {
            'branch_id': request.POST.get('branch_id'),
            'pickup_time': request.POST.get('pickup_time', ''),
        }
    }
    request.session['order_data'] = pickup_data
    return redirect(request.META.get('HTTP_REFERER', '/'))


@require_POST
def save_delivery_details(request):
    delivery_data = {
        'order_method': 'delivery',
        'delivery': {
            'address': request.POST.get('address'),
            'city': request.POST.get('city'),
            'delivery_time': request.POST.get('delivery_time', ''),
        }
    }
    request.session['order_data'] = delivery_data
    return redirect(request.META.get('HTTP_REFERER', '/'))
