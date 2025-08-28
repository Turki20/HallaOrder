from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, Http404
from django.apps import apps
from django.core.exceptions import FieldError
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from menu.models import Product
from .models import Website



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


def site_home(request, slug):
    
    return redirect("websites:menu", slug=slug)


def menu_view(request, slug):
    website = get_object_or_404(Website.objects.select_related("restaurant"), slug=slug)
    # products = _get_products_for(website.restaurant)
    categories = website.restaurant.category_set.all()
    products = []
    for category in categories:
        for p in category.product_set.all():
            products.append(p)

    return render(
        request,
        "websites/menu.html",
        {'website':website, 'products':products, 'current_tab': 'menu'}
    )


def product_detail(request, slug, product_id):
    website = get_object_or_404(Website.objects.select_related("restaurant"), slug=slug)
    product = Product.objects.get(id=product_id)
    return render(
        request,
        "websites/product_detail.html",
        {'website':website, 'p': product, 'current_tab': "menu"}
    )



@require_POST
def add_to_cart(request, slug, product_id):

    website = get_object_or_404(Website, slug=slug)
    p = Product.objects.get(id=product_id)
    cart = _get_cart(request, website)

    if request.method == 'POST':
        qty = request.POST.get("qty", "1")
        try:
            qty = max(int(qty), 1)
        except (TypeError, ValueError):
            qty = 1

        item = {
            "id": p.id,
            "name":str( p.name),
            "price": str(p.price),
            "qty": qty,
            "size": request.POST.get("size", ""),            
            "addons": request.POST.getlist("addons"),     
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
