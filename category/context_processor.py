from django.db.models import Case, When
from .models import Category

def menu_links(request):
    # Force a deliberate display order (Shoes, then Clothes, then anything else)
    # instead of relying on database insertion order.
    order = Case(
        When(slug='shoes', then=0),
        When(slug='shirts', then=1),
        default=2,
    )
    links = Category.objects.all().order_by(order)
    return dict(links=links)

