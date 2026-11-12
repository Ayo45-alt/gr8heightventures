import urllib.parse
from django.shortcuts import render, redirect
from store.models import Product, Variation
from .models import Cart, CartItem, get_variation_max_stock
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
from django.db.models import Sum
from django.views.decorators.http import require_POST



def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart



def _get_cart_count(request):
    """Return total qty of items in the user's cart."""
    if request.user.is_authenticated:
        items = CartItem.objects.filter(
            user=request.user,
            is_active=True,
        )
    else:
        cart_id = _cart_id(request)
        items = CartItem.objects.filter(
            cart__cart_id=cart_id,
            is_active=True,
        )
    return items.aggregate(total=Sum('quantity'))['total'] or 0


def _get_cart_items(request):
    if request.user.is_authenticated:
        return CartItem.objects.filter(user=request.user, is_active=True).select_related('product')

    cart = Cart.objects.filter(cart_id=_cart_id(request)).first()
    if cart is None:
        return CartItem.objects.none()
    return CartItem.objects.filter(cart=cart, is_active=True).select_related('product')


def add_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product_variation = []
    added_to_cart = False
    
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
                    added_to_cart = True
            elif max_qty > 0:
                item = CartItem.objects.create(product=product, quantity=1, user=request.user)
                if len(product_variation) > 0:
                    item.variations.clear()
                    item.variations.add(*product_variation)
                item.save()
                added_to_cart = True
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
            added_to_cart = True
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            if not added_to_cart:
                return JsonResponse(
                    {'status': 'error', 'message': 'No more stock is available for this selection.'},
                    status=400,
                )
            return JsonResponse({'status': 'ok', 'cart_count': _get_cart_count(request)})
        if request.POST.get('order_via_whatsapp'):
            return redirect('cart')
        if request.POST.get('stay_on_product_page'):
            if added_to_cart:
                messages.success(request, 'Added to Bag', extra_tags='bag-added')
            return redirect(product.get_url())
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
                    added_to_cart = True
            elif max_qty > 0:
                item = CartItem.objects.create(product=product, quantity=1, cart=cart)
                if len(product_variation) > 0:
                    item.variations.clear()
                    item.variations.add(*product_variation)
                item.save()
                added_to_cart = True
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
            added_to_cart = True
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            if not added_to_cart:
                return JsonResponse(
                    {'status': 'error', 'message': 'No more stock is available for this selection.'},
                    status=400,
                )
            return JsonResponse({'status': 'ok', 'cart_count': _get_cart_count(request)})
        if request.POST.get('order_via_whatsapp'):
            return redirect('cart')
        if request.POST.get('stay_on_product_page'):
            if added_to_cart:
                messages.success(request, 'Added to Bag', extra_tags='bag-added')
            return redirect(product.get_url())
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
    cart_items = _get_cart_items(request)
    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity

    tax = 0
    grand_total = total

    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total,
    }
    return render(request, 'store/cart.html', context)


@require_POST
def order_whatsapp(request):
    customer_name = request.POST.get('customer_name', '').strip()
    delivery_address = request.POST.get('delivery_address', '').strip()

    if not customer_name or not delivery_address:
        messages.error(request, 'Please enter your name and delivery address to continue.')
        return redirect('cart')

    cart_items = _get_cart_items(request)
    if not cart_items.exists():
        messages.error(request, 'Your Bag is empty. Add an item before placing an order.')
        return redirect('cart')

    total = sum(item.product.price * item.quantity for item in cart_items)
    lines = [
        "Hello Kemi's Shop! 👋",
        'I would like to order the following items from your boutique:',
        '',
        f'Name: {customer_name}',
        f'Delivery address: {delivery_address}',
        '',
        'Order:',
    ]
    for idx, item in enumerate(cart_items, 1):
        variations = item.variations.all()
        var_str = ', '.join(
            f'{variation.variation_category.capitalize()}: {variation.variation_value}'
            for variation in variations
        )
        var_info = f' [{var_str}]' if var_str else ''
        lines.append(
            f'{idx}. {item.product.product_name}{var_info} x{item.quantity} - '
            f'₦{item.product.price * item.quantity:,.0f}'
        )
    lines.extend([
        '',
        f'Subtotal: ₦{total:,.0f}',
        'Please confirm item availability and delivery arrangements. Thank you!',
    ])
    whatsapp_url = (
        "https://wa.me/2348130707949?text="
        f"{urllib.parse.quote(chr(10).join(lines))}"
    )
    return redirect(whatsapp_url)


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