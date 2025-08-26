# orders/views.py
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, NoReverseMatch
from .models import Order, OrderStatus ,OrderItem
from restaurants.models import Branch, Restaurant
from django.http import HttpResponseForbidden


# ---- helpers ---------------------------------------------------------------

STATUS_FLOW = {
    "New": "Preparing",
    "Preparing": "Ready",
    "Ready": "Delivered",
}

def _rev(name: str, **kwargs) -> str:
    """
    Reverse a URL name whether it's namespaced or not.
    Tries plain name first, then 'orders:<name>'.
    """
    try:
        return reverse(name, kwargs=kwargs)
    except NoReverseMatch:
        return reverse(f"orders:{name}", kwargs=kwargs)

def _user_default_branch(user):
    """
    Pick a default Branch for the current user:
      1) If user has one-to-one owned restaurant: user.restaurants -> first branch
      2) If user has multiple owned restaurants (restaurants_owned): first -> first branch
      3) Fallback: first branch in DB (admin/superuser)
    Adjust related_name if your models differ.
    """
    # one-to-one (per your current Restaurant model)
    owner_one = getattr(user, "restaurants", None)
    if isinstance(owner_one, Restaurant):
        b = Branch.objects.filter(restaurant=owner_one).order_by("id").first()
        if b:
            return b

    # fallback: many-owned
    owner_many = getattr(user, "restaurants_owned", None)
    if owner_many and hasattr(owner_many, "first"):
        rest = owner_many.first()
        if isinstance(rest, Restaurant):
            b = Branch.objects.filter(restaurant=rest).order_by("id").first()
            if b:
                return b

    # final fallback
    return Branch.objects.order_by("id").first()

# ---- views ----------------------------------------------------------------

@login_required
def order_board_default(request):
    """
    /board/ → find default branch, then redirect to /board/<branch_id>/
    """
    branch = _user_default_branch(request.user)
    if branch:
        return redirect(_rev("order_board_by_branch", branch_id=branch.id))

    messages.warning(request, "لا يوجد أي فرع محدد. رجاءً أنشئ فرعًا أولاً.")
    # change "branches" below to your actual branches list url name if different
    try:
        return redirect("branches")
    except NoReverseMatch:
        return redirect("/branches/")

@login_required
def order_board(request, branch_id: int | None = None):
    branch_from_query = request.GET.get("branch")
    if branch_from_query and (branch_id is None or str(branch_id) != str(branch_from_query)):
        return redirect("orders:order_board_by_branch", branch_id=int(branch_from_query))

    # allowed branches per role (your code)
    if hasattr(request.user, "role") and request.user.role in ["Cashier", "KitchenStaff"]:
        branches = Branch.objects.filter(employees__user=request.user).distinct()
    elif hasattr(request.user, "role") and request.user.role == "RestaurantOwner":
        branches = Branch.objects.filter(restaurant__owner=request.user)
    else:
        branches = Branch.objects.all()

    active_branch = None
    if branch_id is not None:
        active_branch = get_object_or_404(branches, pk=branch_id)

    qs = (Order.objects.select_related("customer", "branch")
                     .filter(branch__in=branches)
                     .order_by("-created_at"))
    if active_branch:
        qs = qs.filter(branch=active_branch)

    context = {
        "branches": branches,
        "active_branch": active_branch,
        "new_orders": qs.filter(status=OrderStatus.NEW),
        "preparing_orders": qs.filter(status=OrderStatus.PREPARING),
        "ready_orders": qs.filter(status=OrderStatus.READY),
        "advanceable_statuses": [OrderStatus.NEW, OrderStatus.PREPARING, OrderStatus.READY],
        "current_page": "orders:order_board", 
    }
    return render(request, "orders/board.html", context)

@login_required
def order_detail(request, pk: int):
    order = (
        Order.objects.select_related("customer", "branch")
        .prefetch_related("items__product")
        .get(pk=pk)
    )
    return render(request, "orders/detail.html", {"order": order})

@login_required
def advance_status(request, pk: int):
    """
    Advance: New → Preparing → Ready → Delivered
    """
    if request.method != "POST":
        # allow GET fallback during testing; you can enforce POST only
        pass

    order = get_object_or_404(Order, pk=pk)
    nxt = STATUS_FLOW.get(order.status)
    if not nxt:
        messages.info(request, "لا يمكن نقل الطلب من حالته الحالية.")
        return redirect(_rev("order_board_by_branch", branch_id=order.branch_id))

    order.status = nxt
    order.save(update_fields=["status"])
    messages.success(request, f"تم نقل الطلب #{order.pk} إلى {nxt}.")
    return redirect(_rev("order_board_by_branch", branch_id=order.branch_id))

@login_required
def cancel_order(request, pk: int):
    if request.method != "POST":
        # allow GET fallback during testing; you can enforce POST only
        pass

    order = get_object_or_404(Order, pk=pk)
    if order.status in (OrderStatus.DELIVERED, OrderStatus.CANCELLED):
        messages.info(request, "لا يمكن إلغاء هذا الطلب.")
        return redirect(_rev("order_board_by_branch", branch_id=order.branch_id))

    order.status = OrderStatus.CANCELLED
    order.save(update_fields=["status"])
    messages.warning(request, f"تم إلغاء الطلب #{order.pk}.")
    return redirect(_rev("order_board_by_branch", branch_id=order.branch_id))

def _allowed_branches_for(user):
    if hasattr(user, "role") and user.role in ["Cashier", "KitchenStaff"]:
        return Branch.objects.filter(employees__user=user).distinct()
    elif hasattr(user, "role") and user.role == "RestaurantOwner":
        return Branch.objects.filter(restaurant__owner=user)
    return Branch.objects.all()

def order_detail_fragment(request, pk: int):
    allowed = _allowed_branches_for(request.user)

    order = get_object_or_404(
        Order.objects.select_related("customer", "branch"),
        pk=pk,
        branch__in=allowed,
    )

    items = (
        OrderItem.objects
        .select_related("product")
        .filter(order=order)
        .order_by("id")
    )

    return render(request, "orders/_order_detail.html", {"order": order, "items": items})