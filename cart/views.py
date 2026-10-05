import urllib.parse
from django.shortcuts import render, redirect
from store.models import Product, Variation
from .models import Cart, CartItem, get_variation_max_stock
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist



def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart


def add_cart(request, product_id):
    product = Product.objects.get(id=product_id)
    product_variation = []
    
    if request.method == 'POST':
        for item in request.POST:
            key = item
            value = request.POST[key]
            
            if key.lower() in ('color', 'size') and value:
                variation = Variation.objects.filter(
                    product=product,
                    variation_category__iexact=key,
                    variation_value__iexact=value
                ).first()
                if not variation:
                    variation = Variation.objects.create(
                        product=product,
                        variation_category=key.lower(),
                        variation_value=value,
                        is_active=True
                    )
                product_variation.append(variation)

    max_qty = get_variation_max_stock(product, product_variation)

    # Check if user is authenticated
    if request.user.is_authenticated:
        is_cart_item_exists = CartItem.objects.filter(product=product, user=request.user).exists()
        
        if is_cart_item_exists:
            cart_item = CartItem.objects.filter(product=product, user=request.user)
            
            ex_var_list = []
            id = []
            for item in cart_item:
                existing_variation = item.variations.all()
                ex_var_list.append(list(existing_variation))
                id.append(item.id)

            if product_variation in ex_var_list:
                index = ex_var_list.index(product_variation)
                item_id = id[index]
                item = CartItem.objects.get(product=product, id=item_id)
                if item.quantity < max_qty:
                    item.quantity += 1
                    item.save()
            elif max_qty > 0:
                item = CartItem.objects.create(product=product, quantity=1, user=request.user)
                if len(product_variation) > 0:
                    item.variations.clear()
                    item.variations.add(*product_variation)
                item.save()
        elif max_qty > 0:
            cart_item = CartItem.objects.create(
                product=product,
                quantity=1,
                user=request.user,
            )
            if len(product_variation) > 0:
                cart_item.variations.clear()
                cart_item.variations.add(*product_variation)
            cart_item.save()
        return redirect('cart')
    else:
        # For guest users (session-based cart)
        try:
            cart = Cart.objects.get(cart_id=_cart_id(request))
        except Cart.DoesNotExist:
            cart = Cart.objects.create(
                cart_id=_cart_id(request)
            )
        cart.save()

        is_cart_item_exists = CartItem.objects.filter(product=product, cart=cart).exists()
        
        if is_cart_item_exists:
            cart_item = CartItem.objects.filter(product=product, cart=cart)
            
            ex_var_list = []
            id = []
            for item in cart_item:
                existing_variation = item.variations.all()
                ex_var_list.append(list(existing_variation))
                id.append(item.id)

            if product_variation in ex_var_list:
                index = ex_var_list.index(product_variation)
                item_id = id[index]
                item = CartItem.objects.get(product=product, id=item_id)
                if item.quantity < max_qty:
                    item.quantity += 1
                    item.save()
            elif max_qty > 0:
                item = CartItem.objects.create(product=product, quantity=1, cart=cart)
                if len(product_variation) > 0:
                    item.variations.clear()
                    item.variations.add(*product_variation)
                item.save()
        elif max_qty > 0:
            cart_item = CartItem.objects.create(
                product=product,
                quantity=1,
                cart=cart,
            )
            if len(product_variation) > 0:
                cart_item.variations.clear()
                cart_item.variations.add(*product_variation)
            cart_item.save()
        return redirect('cart')
    

def remove_cart(request, cart_item_id):
    if request.user.is_authenticated:
        cart_item = get_object_or_404(CartItem, id=cart_item_id, user=request.user)
    else:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_item = get_object_or_404(CartItem, id=cart_item_id, cart=cart)
    
    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
    else:
        cart_item.delete()
    return redirect('cart')


def remove_cart_item(request, cart_item_id):
    if request.user.is_authenticated:
        cart_item = get_object_or_404(CartItem, id=cart_item_id, user=request.user)
    else:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_item = get_object_or_404(CartItem, id=cart_item_id, cart=cart)
    
    cart_item.delete()
    return redirect('cart')


def cart(request, total=0, quantity=0, cart_items=None):
    try:
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True).select_related('product')
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True).select_related('product')
        
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
    except ObjectDoesNotExist:
        cart_items = []

    tax = 0
    grand_total = total

    # Format pre-filled WhatsApp message for whole cart
    if cart_items:
        lines = ["Hello Kemi's Shop! 👋", "I would like to order the following items from your boutique:\n"]
        for idx, item in enumerate(cart_items, 1):
            variations = item.variations.all()
            var_str = ", ".join([f"{v.variation_category.capitalize()}: {v.variation_value}" for v in variations]) if variations else ""
            var_info = f" [{var_str}]" if var_str else ""
            lines.append(f"{idx}. {item.product.product_name}{var_info} x{item.quantity} - ₦{item.product.price * item.quantity:,.0f}")
        lines.append(f"\nSubtotal: ₦{total:,.0f}")
        lines.append("Please confirm item availability and delivery arrangements. Thank you!")
        wa_text = "\n".join(lines)
        whatsapp_cart_url = f"https://wa.me/2348130707949?text={urllib.parse.quote(wa_text)}"
    else:
        whatsapp_cart_url = "https://wa.me/2348130707949"

    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total,
        'whatsapp_cart_url': whatsapp_cart_url,
    }
    return render(request, 'store/cart.html', context)


from django.shortcuts import render, redirect
from .models import Cart, CartItem
from .views import _cart_id
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required

@login_required(login_url='login')
def checkout(request, total=0, quantity=0, cart_items=None):
    try:
        tax = 0
        grand_total = 0
        
        cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
        
        tax = (2 * total) / 100
        grand_total = total + tax
    except ObjectDoesNotExist:
        pass
    
    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total,
    }
    return render(request, 'store/checkout.html', context)