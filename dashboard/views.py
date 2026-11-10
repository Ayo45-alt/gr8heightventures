import os
from datetime import timedelta

from django.contrib import auth
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from analytics.models import DailyPageView
from orders.models import Order
from store.models import Product
from .forms import ProductEditForm


staff_required = user_passes_test(
    lambda user: user.is_authenticated and user.is_staff,
    login_url='owner-login',
)


def owner_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if not user.is_staff:
                form.add_error(None, 'This account does not have dashboard access.')
            else:
                auth.login(request, user)
                next_url = request.POST.get('next') or request.GET.get('next')
                if next_url and url_has_allowed_host_and_scheme(
                    next_url,
                    allowed_hosts={request.get_host()},
                    require_https=request.is_secure(),
                ):
                    return redirect(next_url)
                return redirect('owner-dashboard')
    else:
        form = AuthenticationForm(request)

    return render(request, 'dashboard/login.html', {
        'form': form,
        'next': request.GET.get('next', ''),
    })


@staff_required
def owner_dashboard(request):
    today = timezone.localdate()
    chart_start = today - timedelta(days=29)
    chart_records = dict(
        DailyPageView.objects.filter(day__gte=chart_start, day__lte=today)
        .values_list('day', 'views')
    )
    chart_days = [
        {
            'day': chart_start + timedelta(days=offset),
            'views': chart_records.get(chart_start + timedelta(days=offset), 0),
        }
        for offset in range(30)
    ]
    max_chart_views = max((item['views'] for item in chart_days), default=0)
    for item in chart_days:
        item['height'] = (
            round(item['views'] * 100 / max_chart_views)
            if max_chart_views
            else 0
        )

    daily_views = DailyPageView.objects.all()
    page_view_total = daily_views.aggregate(total=Sum('views'))['total'] or 0
    today_views = daily_views.filter(day=today).values_list('views', flat=True).first() or 0

    product_page = Paginator(
        Product.objects.select_related('category').order_by('product_name'), 20
    ).get_page(request.GET.get('products'))
    order_page = Paginator(
        Order.objects.filter(is_ordered=True).order_by('-created_at'), 10
    ).get_page(request.GET.get('orders'))

    return render(request, 'dashboard/index.html', {
        'today': today,
        'today_views': today_views,
        'page_view_total': page_view_total,
        'tracked_days': daily_views.count(),
        'traffic_storage_warning': (
            os.environ.get('VERCEL')
            and settings.DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3'
        ),
        'chart_days': chart_days,
        'daily_views': daily_views,
        'products': product_page,
        'orders': order_page,
        'order_status_choices': Order.STATUS,
        'product_count': Product.objects.count(),
        'order_count': Order.objects.filter(is_ordered=True).count(),
    })


@staff_required
def edit_product(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    if request.method == 'POST':
        form = ProductEditForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f'{product.product_name} was updated.')
            return redirect('owner-dashboard')
    else:
        form = ProductEditForm(instance=product)

    return render(request, 'dashboard/edit_product.html', {
        'form': form,
        'product': product,
    })


@staff_required
@require_POST
def update_order_status(request, order_id):
    order = get_object_or_404(Order, pk=order_id, is_ordered=True)
    new_status = request.POST.get('status')
    valid_statuses = {value for value, _ in Order.STATUS}
    if new_status not in valid_statuses:
        messages.error(request, 'Choose a valid order status.')
        return redirect('owner-dashboard')

    order.status = new_status
    order.save(update_fields=['status', 'updated_at'])
    messages.success(request, f'Order {order.order_number} status updated.')
    return redirect('owner-dashboard')


@require_POST
def owner_logout(request):
    auth.logout(request)
    return redirect('owner-login')
