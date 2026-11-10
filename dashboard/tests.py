from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from analytics.models import DailyPageView
from category.models import Category
from orders.models import Order
from store.models import Product


class OwnerDashboardTests(TestCase):
    def test_dashboard_requires_staff_login(self):
        response = self.client.get(reverse('owner-dashboard'))

        self.assertRedirects(
            response,
            f"{reverse('owner-login')}?next={reverse('owner-dashboard')}",
        )

    def test_staff_user_can_view_dashboard(self):
        user = get_user_model().objects.create_user(
            first_name='Shop',
            last_name='Owner',
            username='shopowner',
            email='owner@example.com',
            password='test-password-123',
        )
        user.is_staff = True
        user.save(update_fields=['is_staff'])
        DailyPageView.objects.create(day='2026-01-01', views=12)
        category = Category.objects.create(category_name='Shoes', slug='shoes')
        Product.objects.create(
            product_name='Everyday Sneakers',
            slug='everyday-sneakers',
            price=80,
            stock=4,
            category=category,
            images='photos/products/sneakers.jpg',
        )
        Order.objects.create(
            user=user,
            order_number='ORDER-123',
            first_name='Private',
            last_name='Customer',
            phone='0000000000',
            email='private@example.com',
            address_line_1='Private address',
            country='Nigeria',
            state='Lagos',
            city='Lagos',
            order_total=80,
            tax=0,
            is_ordered=True,
        )
        self.client.force_login(user)

        response = self.client.get(reverse('owner-dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Total page views')
        self.assertContains(response, '12')
        self.assertContains(response, 'Everyday Sneakers')
        self.assertContains(response, 'ORDER-123')
        self.assertNotContains(response, 'private@example.com')

    def test_regular_user_cannot_sign_in_to_owner_dashboard(self):
        user = get_user_model().objects.create_user(
            first_name='Shop',
            last_name='Customer',
            username='customer',
            email='customer@example.com',
            password='test-password-123',
        )

        response = self.client.post(reverse('owner-login'), {
            'username': user.email,
            'password': 'test-password-123',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'does not have dashboard access')
        self.assertFalse(response.wsgi_request.user.is_authenticated)
