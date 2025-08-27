def cart_info(request):
    cart = request.session.get("cart", {})
    try:
        count = sum(int(item.get("qty", 0)) for item in cart.values())
    except Exception:
        count = 0
    return {"cart_count": count}
