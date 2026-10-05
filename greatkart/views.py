from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse
from django.template.loader import render_to_string
from store.models import Product
from store.views import get_interleaved_catalog

def home(request):
    all_products = get_interleaved_catalog()
    product_count = len(all_products)
    per_page = int(request.GET.get('per_page', 16))
    paginator = Paginator(all_products, per_page)
    page = request.GET.get('page', 1)

    try:
        paged_products = paginator.page(page)
    except PageNotAnInteger:
        paged_products = paginator.page(1)
    except EmptyPage:
        paged_products = paginator.page(paginator.num_pages)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax') == '1':
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
        'products': paged_products,
        'product_count': product_count,
    }
    return render(request, 'home.html', context)


def about(request):
    return render(request, 'pages/about.html')


def contact(request):
    return render(request, 'pages/contact.html')


def delivery(request):
    return render(request, 'pages/delivery.html')


def returns_policy(request):
    return render(request, 'pages/returns.html')


def faqs(request):
    return render(request, 'pages/faqs.html')


def privacy(request):
    return render(request, 'pages/privacy.html')


def terms(request):
    return render(request, 'pages/terms.html')