from django.db.models import Case, When, IntegerField
from .models import Category

def menu_links(request):
    order = Case(
        When(slug='shoes', then=0),
        When(slug='dresses', then=1),
        When(slug='tops', then=2),
        When(slug='trousers', then=3),
        When(slug='jackets', then=4),
        default=5,
        output_field=IntegerField(),
    )
    links = Category.objects.order_by(order)
    return {'links': links}
