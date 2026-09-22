from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Cart, CartDetail
from products.models import Snack

def get_cart(user):
    cart, created = Cart.objects.get_or_create(user=user)
    return cart

@login_required
def cart_detail(request):
    cart = get_cart(request.user)
    return render(request, 'cart/cart.html', {'cart': cart})

def cart_add(request, snack_id):
    if not request.user.is_authenticated:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False, 
                'login_required': True, 
                'redirect_url': f"/accounts/login/?next={request.META.get('HTTP_REFERER', '/')}"
            })
        return redirect(f"/accounts/login/?next={request.path}")

    cart = get_cart(request.user)
    snack = get_object_or_404(Snack, id=snack_id)
    quantity = int(request.POST.get('quantity', 1))
    
    cart_item, created = CartDetail.objects.get_or_create(
        cart=cart, 
        snack=snack,
        defaults={'unitPrice': snack.price, 'totalPrice': snack.price * quantity, 'quantity': quantity}
    )
    if not created:
        cart_item.quantity += quantity
        cart_item.save()
        
    update_cart_total(cart)
    
    # AJAX request: return JSON instead of redirecting
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        cart_count = cart.items.count()
        return JsonResponse({'success': True, 'cart_item_count': cart_count})
    
    action = request.POST.get('action')
    if action == 'buy_now':
        return redirect('orders:checkout')
    return redirect('cart:cart_detail')

@login_required
def cart_remove(request, item_id):
    cart = get_cart(request.user)
    item = get_object_or_404(CartDetail, id=item_id, cart=cart)
    item.delete()
    update_cart_total(cart)
    return redirect('cart:cart_detail')

@login_required
def cart_update(request, item_id):
    cart = get_cart(request.user)
    item = get_object_or_404(CartDetail, id=item_id, cart=cart)
    quantity = int(request.POST.get('quantity', 1))
    if quantity > 0:
        item.quantity = quantity
        item.save()
    else:
        item.delete()
    update_cart_total(cart)
    return redirect('cart:cart_detail')

def update_cart_total(cart):
    total = sum(item.totalPrice for item in cart.items.all())
    cart.totalAmount = total
    cart.save()
