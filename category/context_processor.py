from django.db.models import Case, When, Count, Q
from .models import Category
from store.models import Product

def menu_links(request):
    order = Case(
        When(slug='shoes', then=0),
        When(slug='dresses', then=1),
        When(slug='tops', then=2),
        When(slug='trousers', then=3),
        When(slug='jackets', then=4),
        default=5,
    )
    links = Category.objects.annotate(
        prod_count=Count('product', filter=Q(product__is_available=True))
    ).order_by(order)
    
    total_catalog_count = Product.objects.filter(is_available=True).count()
    all_clothing_count = Product.objects.filter(is_available=True).exclude(category__slug='shoes').count()
    return dict(links=links, total_catalog_count=total_catalog_count, all_clothing_count=all_clothing_count)
