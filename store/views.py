import json
import urllib.parse
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import Product, ReviewRating, ProductGallery, Wishlist
from category.models import Category
from cart.models import CartItem
from cart.views import _cart_id
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q, Avg, Count
from django.contrib import messages
from .forms import ReviewForm
from .context_processors import _get_session_key
from orders.models import OrderProduct

COLORWAYS_CONFIG = {
    220: [ # Chelsea & Violet Strappy Cage Sandal Heel
        {
            'color_id': 'black',
            'display_name': 'Black Wet-Look',
            'price': 48000,
            'formatted_price': '₦48,000',
            'image': '/media/photos/products/kemi-s15-chelsea-and-violet-black-cage.jpg',
            'gallery_images': [
                '/media/photos/products/kemi-s15-chelsea-and-violet-black-cage.jpg',
                '/media/store/product_gallery/prod_220_black_cage_hd_2.jpg',
            ],
            'sizes': ['EU 40 (US 9)', 'EU 40-41 (US 9.5)'],
            'stock': 3,
            'stock_text': '3 pairs in stock (EU 40 & EU 40-41)',
            'hex': '#1c1c1e',
        },
        {
            'color_id': 'gold',
            'display_name': 'Mirror Gold Metallic',
            'price': 54000,
            'formatted_price': '₦54,000',
            'image': '/media/photos/products/prod_220_gold_cage_hd_1.jpg',
            'gallery_images': [
                '/media/photos/products/prod_220_gold_cage_hd_1.jpg',
                '/media/store/product_gallery/prod_220_gold_cage_hd_2.jpg',
            ],
            'sizes': ['EU 40-41 (US 9.5)'],
            'stock': 1,
            'stock_text': '1 pair in stock (EU 40-41 / US 9.5)',
            'hex': '#d4af37',
        }
    ],
    206: [ # Gianni Bini Patent Block Heel Sandal
        {
            'color_id': 'lavender',
            'display_name': 'Lavender / Lilac Patent',
            'price': 27500,
            'formatted_price': '₦27,500',
            'image': '/media/photos/products/prod_206_lavender_pair_main.jpg',
            'gallery_images': [
                '/media/photos/products/prod_206_lavender_pair_main.jpg',
                '/media/store/product_gallery/prod_206_lavender_pair_front.jpg',
            ],
            'sizes': ['EU 40-41 (US 9.5)'],
            'stock': 3,
            'stock_text': '3 pairs in stock (EU 40-41 / US 9.5)',
            'hex': '#b590ca',
        },
        {
            'color_id': 'carton',
            'display_name': 'Carton Cream / Nude Patent',
            'price': 27500,
            'formatted_price': '₦27,500',
            'image': '/media/photos/products/prod_206_carton_pair_main.jpg',
            'gallery_images': [
                '/media/photos/products/prod_206_carton_pair_main.jpg',
                '/media/store/product_gallery/prod_206_carton_pair_front.jpg',
            ],
            'sizes': ['EU 41 (US 10)'],
            'stock': 1,
            'stock_text': '1 pair in stock (EU 41 / US 10)',
            'hex': '#e6cca9',
        }
    ],
    212: [ # Gianni Bini Glitter Ankle-Strap Platform Heel
        {
            'color_id': 'silver',
            'display_name': 'Silver Glitter',
            'price': 45000,
            'formatted_price': '₦45,000',
            'image': '/media/photos/products/kemi-s7-gianni-bini-glitter-strap-heel.webp',
            'sizes': ['EU 42-43 (US 11)'],
            'stock': 1,
            'stock_text': '1 pair in stock (EU 42-43 / US 11)',
            'hex': '#d1d5db',
        },
        {
            'color_id': 'gold',
            'display_name': 'Champagne Gold Glitter',
            'price': 45000,
            'formatted_price': '₦45,000',
            'image': '/media/photos/products/kemi-s7-gold-gianni-bini-glitter-strap.jpg',
            'sizes': ['EU 42-43 (US 11)'],
            'stock': 1,
            'stock_text': '1 pair in stock (EU 42-43 / US 11)',
            'hex': '#e2c98d',
        }
    ],
    237: [ # Classic Double Buckle Monk Strap Shoes
        {
            'color_id': 'brown',
            'display_name': 'Cognac Brown Leather',
            'price': 95000,
            'formatted_price': '₦95,000',
            'image': '/media/photos/products/prod_237_brown_monk_hd_1.jpg',
            'gallery_images': [
                '/media/photos/products/prod_237_brown_monk_hd_1.jpg',
                '/media/store/product_gallery/prod_237_brown_monk_hd_2.jpg',
            ],
            'sizes': ['EU 43.5 (US 10.5)'],
            'stock': 1,
            'stock_text': '1 pair in stock (EU 43.5 / US 10.5)',
            'hex': '#6f3918',
        },
        {
            'color_id': 'black',
            'display_name': 'Jet Black Leather',
            'price': 95000,
            'formatted_price': '₦95,000',
            'image': '/media/photos/products/prod_237_black_monk_hd_1.jpg',
            'gallery_images': [
                '/media/photos/products/prod_237_black_monk_hd_1.jpg',
                '/media/store/product_gallery/prod_237_black_monk_hd_2.jpg',
            ],
            'sizes': ['EU 44.5 (US 11.5)'],
            'stock': 1,
            'stock_text': '1 pair in stock (EU 44.5 / US 11.5)',
            'hex': '#111111',
        }
    ],
    239: [ # Gibson & Latimer One Shoulder Dress
        {
            'color_id': 'gold_navy',
            'display_name': 'Gold & Navy Shimmer',
            'price': 38000,
            'formatted_price': '₦38,000',
            'image': '/media/photos/products/prod_239_gold_navy_main.jpg',
            'gallery_images': [
                '/media/photos/products/prod_239_gold_navy_main.jpg',
                '/media/store/product_gallery/prod_239_gold_navy_closeup.jpg',
            ],
            'sizes': ['L (UK 16)', 'XXL (UK 20-22)'],
            'size_prices': {'L (UK 16)': '₦38,000', 'XXL (UK 20-22)': '₦40,000'},
            'stock': 5,
            'stock_text': '5 pieces in stock (Sizes L & XXL)',
            'hex': '#b59d57',
        },
        {
            'color_id': 'silver_navy',
            'display_name': 'Silver & Navy Shimmer',
            'price': 38000,
            'formatted_price': '₦38,000',
            'image': '/media/photos/products/prod_239_silver_navy_main.jpg',
            'gallery_images': [
                '/media/photos/products/prod_239_silver_navy_main.jpg',
                '/media/store/product_gallery/prod_239_silver_navy_closeup.jpg',
            ],
            'sizes': ['XL (UK 18-20)'],
            'stock': 1,
            'stock_text': '1 piece in stock (Size XL / UK 18-20)',
            'hex': '#9ca3af',
        }
    ],
    164: [ # Preston & York Metallic Sequin Long Sleeve Shift Dress
        {
            'color_id': 'gold',
            'display_name': 'Gold',
            'price': 40000,
            'formatted_price': '₦40,000',
            'image': '/media/photos/products/prod_164_gold_sequin_v3.jpg',
            'gallery_images': [
                '/media/photos/products/prod_164_gold_sequin_v3.jpg',
                '/media/store/product_gallery/prod_164_gold_back_v3.jpg',
                '/media/store/product_gallery/prod_164_gold_tag_v3.jpg',
            ],
            'sizes': ['UK 14 (US 10)', 'UK 20 (US 16)', 'UK 22 (US 18)'],
            'size_prices': {'UK 14 (US 10)': '₦40,000', 'UK 20 (US 16)': '₦46,000', 'UK 22 (US 18)': '₦48,000'},
            'stock': 7,
            'stock_text': 'In Stock • Ready to dispatch in Lagos',
            'hex': '#d4af37',
        },
        {
            'color_id': 'champagne',
            'display_name': 'Champagne',
            'price': 44000,
            'formatted_price': '₦44,000',
            'image': '/media/photos/products/prod_164_champagne_sequin_v3.jpg',
            'gallery_images': [
                '/media/photos/products/prod_164_champagne_sequin_v3.jpg',
                '/media/store/product_gallery/prod_164_champagne_detail_v3.jpg',
            ],
            'sizes': ['UK 18 (US 14)', 'UK 20 (US 16)', 'UK 22 (US 18)'],
            'size_prices': {'UK 18 (US 14)': '₦44,000', 'UK 20 (US 16)': '₦46,000', 'UK 22 (US 18)': '₦48,000'},
            'stock': 7,
            'stock_text': 'In Stock • Ready to dispatch in Lagos',
            'hex': '#e8d3b9',
        }
    ],
    171: [ # Gianni Bini - "Noa" Liquid Metallic Lamé Wrap Dress
        {
            'color_id': 'dark_gold',
            'display_name': 'Dark Gold',
            'price': 28500,
            'formatted_price': '₦28,500',
            'image': '/media/photos/products/prod_171_dark_gold_front_v3.jpg',
            'gallery_images': [
                '/media/photos/products/prod_171_dark_gold_front_v3.jpg',
                '/media/store/product_gallery/prod_171_dark_gold_back_v3.jpg',
                '/media/store/product_gallery/prod_171_dark_gold_flatlay_v3.jpg',
            ],
            'sizes': ['XS (UK 6-8)'],
            'stock': 1,
            'stock_text': 'In Stock • Ready to dispatch in Lagos',
            'hex': '#c5a059',
        },
        {
            'color_id': 'dark_silver',
            'display_name': 'Dark Silver',
            'price': 28500,
            'formatted_price': '₦28,500',
            'image': '/media/photos/products/prod_171_dark_silver_front_v3.jpg',
            'gallery_images': [
                '/media/photos/products/prod_171_dark_silver_front_v3.jpg',
                '/media/store/product_gallery/prod_171_dark_silver_back_v3.jpg',
                '/media/store/product_gallery/prod_171_dark_silver_detail_v3.jpg',
            ],
            'sizes': ['XS (UK 6-8)'],
            'stock': 1,
            'stock_text': 'In Stock • Ready to dispatch in Lagos',
            'hex': '#8e9094',
        }
    ],
    205: [ # Intro Love The Fit - Knit Corduroy Tummy Control Leggings
        {
            'color_id': 'brown',
            'display_name': 'Espresso Brown',
            'price': 22000,
            'formatted_price': '₦22,000',
            'image': '/media/photos/products/prod_205_brown_corduroy_main.jpg',
            'gallery_images': [
                '/media/photos/products/prod_205_brown_corduroy_main.jpg',
                '/media/store/product_gallery/prod_205_brown_corduroy_closeup.jpg',
            ],
            'sizes': ['2X (UK 24-26)'],
            'stock': 1,
            'stock_text': '1 piece in stock (2X / UK 24-26)',
            'hex': '#5e493e',
        },
        {
            'color_id': 'black',
            'display_name': 'Jet Black',
            'price': 22000,
            'formatted_price': '₦22,000',
            'image': '/media/photos/products/prod_205_black_corduroy_main.jpg',
            'gallery_images': [
                '/media/photos/products/prod_205_black_corduroy_main.jpg',
                '/media/store/product_gallery/prod_205_black_corduroy_closeup.jpg',
            ],
            'sizes': ['1X (UK 20-22)'],
            'stock': 1,
            'stock_text': '1 piece in stock (1X / UK 20-22)',
            'hex': '#18181a',
        }
    ]
}

INVENTORY_BREAKDOWN_CONFIG = {
    # Shoes
    206: "4 pairs in stock: 3 pairs Lavender (EU 40-41 / US 9.5), 1 pair Carton Cream (EU 41 / US 10)",
    208: "2 pairs in stock (Both EU 41 / US 10)",
    209: "2 pairs in stock (Both EU 40-41 / US 9.5)",
    210: "2 pairs in stock (Both EU 40-41 / US 9.5)",
    212: "2 pairs in stock: 1 pair Silver Glitter (EU 42-43 / US 11), 1 pair Champagne Gold Glitter (EU 42-43 / US 11)",
    213: "2 pairs in stock: 1 pair EU 40-41 (US 9.5), 1 pair EU 41 (US 10)",
    214: "3 pairs in stock: 2 pairs EU 40-41 (US 9.5), 1 pair EU 41 (US 10)",
    215: "4 pairs in stock: 2 pairs EU 42-43 (US 11), 1 pair EU 40-41 (US 9.5), 1 pair EU 41 (US 10)",
    217: "2 pairs in stock: 1 pair EU 40-41 (US 9.5), 1 pair EU 41 (US 10)",
    218: "2 pairs in stock: 1 pair EU 40 (US 9), 1 pair EU 42-43 (US 11)",
    220: "4 pairs in stock: 3 pairs Black (EU 40 & EU 40-41), 1 pair Mirror Gold (EU 40-41)",
    223: "2 pairs in stock: 1 pair EU 40 (US 9), 1 pair EU 40-41 (US 9.5)",
    229: "3 pairs in stock: EU 40 (1 pair), EU 37 (1 pair), EU 35 (1 pair)",
    236: "2 pairs in stock: 1 pair EU 40-41 (US 9.5), 1 pair EU 35 / Size 3",
    237: "2 pairs in stock: 1 pair Cognac Brown (EU 43.5 / US 10.5), 1 pair Jet Black (EU 44.5 / US 11.5)",

    # Apparel
    238: "5 pieces in stock: 4 pieces in UK 20 / US 16 (₦35,000), 1 piece in UK 18 / US 14 (₦32,000)",
    164: "14 pieces total: Gold (2 in UK 14 [₦40,000], 2 in UK 20 [₦46,000], 3 in UK 22 [₦48,000]) & Champagne (1 in UK 18 [₦44,000], 3 in UK 20 [₦46,000], 3 in UK 22 [₦48,000])",
    166: "2 pieces in stock (Both L / UK 16)",
    239: "6 pieces in stock: Gold & Blue (4 in XXL, 1 in L), Silver & Blue (1 in XL)",
    170: "2 pieces in stock: 1 in 1X (UK 20-22), 1 in Plus X (UK 18-20)",
    171: "2 pieces in stock: 1 in Dark Gold (XS), 1 in Dark Silver (XS)",
    180: "3 pieces in stock: 1 in 1X, 1 in 2X, 1 in 3X",
    181: "2 pieces in stock (Both 3X / UK 26-28)",
    182: "6 pieces in stock: 3 in L (₦13,000), 2 in M (₦12,000), 1 in Petite L (₦13,000)",
    205: "2 pieces in stock: 1 in Espresso Brown (2X), 1 in Jet Black (1X)",
    158: "1 piece in stock (UK 22 / US 18)",
}


def get_interleaved_catalog():
    """
    Returns all available products starting with our 8 premier showcase items,
    followed by the remaining products interleaved across Shoes, Dresses, Tops, and Trousers
    so every row of 4 displays a rich variety of categories.
    """
    premier_ids = [238, 206, 183, 197, 168, 209, 185, 160]
    all_avail = list(Product.objects.filter(is_available=True).select_related('category').order_by('-id'))
    by_id = {p.id: p for p in all_avail}

    ordered = []
    seen = set()
    for pid in premier_ids:
        if pid in by_id:
            ordered.append(by_id[pid])
            seen.add(pid)

    buckets = {'shoes': [], 'dresses': [], 'tops': [], 'trousers': [], 'other': []}
    for p in all_avail:
        if p.id in seen:
            continue
        slug = p.category.slug if p.category else 'other'
        buckets.get(slug, buckets['other']).append(p)

    cat_order = ['shoes', 'dresses', 'tops', 'trousers', 'other']
    while any(buckets[k] for k in cat_order):
        for k in cat_order:
            if buckets[k]:
                ordered.append(buckets[k].pop(0))

    return ordered


def store(request, category_slug=None):
    category = None
    products = None

    if not category_slug:
        category_slug = request.GET.get('category')

    # Price filter
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    # Category filter
    is_all_clothing = False
    if category_slug == 'clothing':
        is_all_clothing = True
        qs = Product.objects.filter(is_available=True).exclude(category__slug='shoes').order_by('-id')
        if min_price and max_price:
            try:
                qs = qs.filter(price__gte=float(min_price), price__lte=float(max_price))
            except ValueError:
                pass
        products = list(qs)
        category = {
            'category_name': 'All Clothing',
            'slug': 'clothing',
            'get_url': '/store/category/clothing/',
        }
    elif category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        qs = Product.objects.filter(category=category, is_available=True).order_by('-id')
        if min_price and max_price:
            try:
                qs = qs.filter(price__gte=float(min_price), price__lte=float(max_price))
            except ValueError:
                pass
        products = list(qs)
    else:
        if min_price and max_price:
            try:
                qs = Product.objects.filter(is_available=True, price__gte=float(min_price), price__lte=float(max_price)).order_by('-id')
                products = list(qs)
            except ValueError:
                products = get_interleaved_catalog()
        else:
            products = get_interleaved_catalog()

    product_count = len(products)

    # Dynamic pagination:
    # 1. ?all=true -> Show all products at once
    # 2. Specific category or 'clothing' -> Show up to 60 (covers 100% of any category without pagination)
    # 3. All products -> Default to 36 (only 3 pages instead of 8)
    show_all = request.GET.get('all') == 'true' or request.GET.get('per_page') == 'all'
    if show_all:
        per_page = 250
    elif category_slug:
        per_page = 60
    else:
        per_page = int(request.GET.get('per_page', 36))

    paginator = Paginator(products, per_page)
    page = request.GET.get('page')

    try:
        paged_products = paginator.page(page)
    except PageNotAnInteger:
        paged_products = paginator.page(1)
    except EmptyPage:
        paged_products = paginator.page(paginator.num_pages)

    # AJAX Load More response
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax') == '1':
        from django.template.loader import render_to_string
        cards_html = render_to_string('store/includes/product_cards_list.html', {
            'products': paged_products,
        }, request=request)
        return JsonResponse({
            'html': cards_html,
            'has_next': paged_products.has_next(),
            'next_page_number': paged_products.next_page_number() if paged_products.has_next() else None,
            'current_count': len(paged_products),
            'total_count': product_count,
        })

    context = {
        'category': category,
        'products': paged_products,
        'product_count': product_count,
        'show_all': show_all,
        'per_page': per_page,
    }
    return render(request, 'store/store.html', context)

def product_detail(request, category_slug, product_slug):
    try:
        single_product = Product.objects.get(category__slug=category_slug, slug=product_slug)
        if request.user.is_authenticated:
            in_cart = CartItem.objects.filter(user=request.user, product=single_product).exists()
        else:
            in_cart = CartItem.objects.filter(cart__cart_id=_cart_id(request), product=single_product).exists()
    except Exception as e:
        raise e
    
    # Check if user ordered this product
    if request.user.is_authenticated:
        orderproduct = OrderProduct.objects.filter(user=request.user, product_id=single_product.id).exists()
    else:
        orderproduct = None
    
    # Get reviews
    reviews = ReviewRating.objects.filter(product_id=single_product.id, status=True).order_by('-created_at')
    review_count = reviews.count()
    
    # Calculate average rating
    if review_count > 0:
        average_rating = reviews.aggregate(Avg('rating'))['rating__avg']
    else:
        average_rating = 0
    
    # Get product gallery images
    product_gallery = ProductGallery.objects.filter(product_id=single_product.id)

    # Colorways options (for multi-color pieces)
    color_options = COLORWAYS_CONFIG.get(single_product.id, [])
    color_options_json = json.dumps(color_options) if color_options else '[]'

    # 1-Click WhatsApp Direct Order URL
    if color_options:
        init_color = color_options[0]
        init_size = f" (Size: {init_color['sizes'][0]})" if init_color['sizes'] else ""
        wa_msg = f"Hello Kemi's Shop! 👋 I would like to order: {single_product.product_name} in {init_color['display_name']}{init_size} for {init_color['formatted_price']}. Is this available?"
    else:
        sizes = single_product.variation_set.sizes()
        size_str = f" (Size: {sizes.first().variation_value})" if sizes.exists() else ""
        wa_msg = f"Hello Kemi's Shop! 👋 I would like to order: {single_product.product_name}{size_str} (Price: ₦{single_product.price:,.0f}). Is this available?"
    whatsapp_url = f"https://wa.me/2348130707949?text={urllib.parse.quote(wa_msg)}"
    
    # Standard customer-facing detail page: no internal inventory breakdown memos
    inventory_breakdown = ''

    context = {
        'single_product': single_product,
        'in_cart': in_cart,
        'orderproduct': orderproduct,
        'reviews': reviews,
        'review_count': review_count,
        'average_rating': average_rating,
        'product_gallery': product_gallery,
        'whatsapp_url': whatsapp_url,
        'color_options': color_options,
        'color_options_json': color_options_json,
        'inventory_breakdown': inventory_breakdown,
    }
    return render(request, 'store/product_detail.html', context)


def search(request):
    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        if keyword:
            products = Product.objects.order_by('-created_date').filter(Q(description__icontains=keyword) | Q(product_name__icontains=keyword))
            product_count = products.count()
            context = {
                'products': products,
                'product_count': product_count,
            }
            return render(request, 'store/store.html', context)
    return render(request, 'store/store.html')

def submit_review(request, product_id):
    url = request.META.get('HTTP_REFERER')
    if request.method == 'POST':
        try:
            reviews = ReviewRating.objects.get(user__id=request.user.id, product__id=product_id)
            form = ReviewForm(request.POST, instance=reviews)
            form.save()
            messages.success(request, 'Thank you! Your review has been updated.')
            return redirect(url)
        except ReviewRating.DoesNotExist:
            form = ReviewForm(request.POST)
            if form.is_valid():
                data = ReviewRating()
                data.subject = form.cleaned_data['subject']
                data.rating = form.cleaned_data['rating']
                data.review = form.cleaned_data['review']
                data.ip = request.META.get('REMOTE_ADDR')
                data.product_id = product_id
                data.user_id = request.user.id
                data.save()
                messages.success(request, 'Thank you! Your review has been submitted.')
                return redirect(url)


def wishlist(request):
    if request.user.is_authenticated:
        wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product', 'product__category')
    else:
        session_key = _get_session_key(request)
        wishlist_items = Wishlist.objects.filter(session_id=session_key).select_related('product', 'product__category')

    items_data = []
    for wi in wishlist_items:
        p = wi.product
        msg = f"Hello Kemi's Shop! 👋 I shortlisted {p.product_name} (₦{p.price:,.0f}) from your boutique lookbook and would like to order it!"
        items_data.append({
            'item': wi,
            'product': p,
            'whatsapp_url': f"https://wa.me/2348130707949?text={urllib.parse.quote(msg)}"
        })

    context = {
        'wishlist_items': items_data,
        'count': len(items_data),
    }
    return render(request, 'store/wishlist.html', context)


def toggle_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.user.is_authenticated:
        existing = Wishlist.objects.filter(user=request.user, product=product).first()
        if existing:
            existing.delete()
            in_wishlist = False
            status = 'removed'
        else:
            Wishlist.objects.create(user=request.user, product=product)
            in_wishlist = True
            status = 'added'
        count = Wishlist.objects.filter(user=request.user).count()
    else:
        session_key = _get_session_key(request)
        existing = Wishlist.objects.filter(session_id=session_key, product=product).first()
        if existing:
            existing.delete()
            in_wishlist = False
            status = 'removed'
        else:
            Wishlist.objects.create(session_id=session_key, product=product)
            in_wishlist = True
            status = 'added'
        count = Wishlist.objects.filter(session_id=session_key).count()

    return JsonResponse({
        'status': status,
        'in_wishlist': in_wishlist,
        'wishlist_count': count,
        'product_name': product.product_name,
    })


def remove_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.user.is_authenticated:
        Wishlist.objects.filter(user=request.user, product=product).delete()
    else:
        session_key = _get_session_key(request)
        Wishlist.objects.filter(session_id=session_key, product=product).delete()
    return redirect('wishlist')