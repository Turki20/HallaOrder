from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, Http404
from django.apps import apps
from django.core.exceptions import FieldError
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from .models import Website


# -------------------- Helpers --------------------
def _get_product_model():
    
    for app_label in ("products", "menu"):
        try:
            return apps.get_model(app_label, "Product")
        except LookupError:
            continue

    for app_config in apps.get_app_configs():
        try:
            Model = app_config.get_model("Product")
            if Model:
                return Model
        except LookupError:
            continue
    return None


def _get_products_for(restaurant):
    
    Model = _get_product_model()
    if not Model:
        return []

    qs = Model.objects.all()

    for filt in (
        {"restaurant": restaurant},
        {"category__restaurant": restaurant},
        {"category__branch__restaurant": restaurant},
    ):
        try:
            data = list(qs.filter(**filt).order_by("id"))
            if data:
                return data
        except FieldError:
            continue

    for filt in ({"is_active": True}, {"available": True}):
        try:
            data = list(qs.filter(**filt).order_by("id")[:48])
            if data:
                return data
        except FieldError:
            continue

    return list(qs.order_by("id")[:48])


def _product_image_url(p):
    
    for attr in ("image", "photo", "thumbnail"):
        img = getattr(p, attr, None)
        if img and getattr(img, "url", ""):
            return img.url
    return ""


def _cart_key(website_id: int) -> str:
    return f"cart_{website_id}"


def _get_cart(request, website):
    return request.session.get(_cart_key(website.id), [])


def _set_cart(request, website, value):
    request.session[_cart_key(website.id)] = value
    request.session.modified = True


def _base_ctx(request, website, **extra):
    cart = _get_cart(request, website)
    cart_count = sum(int(item.get("qty", 1) or 1) for item in cart)
    ctx = {
        "website": website,
        "cart": cart,
        "cart_count": cart_count,
    }
    ctx.update(extra)
    return ctx


# -------------------- Public pages --------------------
def site_home(request, slug):
    
    return redirect("websites:menu", slug=slug)


def menu_view(request, slug):
    website = get_object_or_404(Website.objects.select_related("restaurant"), slug=slug)
    products = _get_products_for(website.restaurant)
    return render(
        request,
        "websites/menu.html",
        _base_ctx(request, website, products=products, current_tab="menu"),
    )


def product_detail(request, slug, pk):
    website = get_object_or_404(Website.objects.select_related("restaurant"), slug=slug)
    Model = _get_product_model()
    if not Model:
        raise Http404("لا يوجد موديل للمنتجات.")
    p = get_object_or_404(Model, pk=pk)
    return render(
        request,
        "websites/product_detail.html",
        _base_ctx(request, website, p=p, current_tab="menu"),
    )


@require_POST
def add_to_cart(request, slug, product_id):

    website = get_object_or_404(Website, slug=slug)
    Model = _get_product_model()
    if not Model:
        return redirect("websites:menu", slug=slug)

    p = get_object_or_404(Model, pk=product_id)
    cart = _get_cart(request, website)

    qty = request.POST.get("qty", "1")
    try:
        qty = max(int(qty), 1)
    except (TypeError, ValueError):
        qty = 1

    item = {
        "id": p.id,
        "name": getattr(p, "name", "منتج"),
        "price": float(getattr(p, "price", 0) or 0),
        "qty": qty,
        "size": request.POST.get("size", ""),            
        "addons": request.POST.getlist("addons"),     
        "image": _product_image_url(p),
    }
    cart.append(item)
    _set_cart(request, website, cart)

    return redirect("websites:menu", slug=slug)


@login_required
def cart_view(request, slug):
 
    website = get_object_or_404(Website, slug=slug)
    cart = _get_cart(request, website)
    total = sum((float(i.get("price", 0)) * int(i.get("qty", 1) or 1)) for i in cart)
    return render(
        request,
        "websites/cart.html",
        _base_ctx(request, website, cart=cart, total=total, current_tab="cart"),
    )


@login_required
def preview_by_pk(request, pk):
    website = get_object_or_404(Website.objects.select_related("restaurant"), pk=pk)
    return redirect("websites:public", slug=website.slug)


@login_required
def preview_my_site(request):
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
