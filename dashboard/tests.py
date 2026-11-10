from io import BytesIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

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
        product = Product.objects.create(
            product_name='Everyday Sneakers',
            slug='everyday-sneakers',
            price=80,
            stock=4,
            category=category,
            images='photos/products/sneakers.jpg',
        )
        order = Order.objects.create(
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
        self.assertContains(response, 'product-thumbnail')
        self.assertContains(response, 'In stock')
        self.assertContains(response, 'ORDER-123')
        self.assertContains(
            response, reverse('owner-product-edit', args=[product.pk])
        )
        self.assertContains(
            response, reverse('owner-order-status', args=[order.pk])
        )
        self.assertNotContains(response, 'private@example.com')

    def test_staff_can_edit_existing_product(self):
        user = self.create_staff_user()
        category = Category.objects.create(category_name='Shoes', slug='shoes')
        product = Product.objects.create(
            product_name='Everyday Sneakers',
            slug='everyday-sneakers',
            price=80,
            stock=4,
            category=category,
            images='photos/products/sneakers.jpg',
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse('owner-product-edit', args=[product.pk]),
            {
                'product_name': 'Classic Sneakers',
                'description': 'Updated description',
                'price': '95',
                'stock': '7',
                'category': str(category.pk),
                'is_available': 'on',
            },
        )

        product.refresh_from_db()
        self.assertRedirects(response, reverse('owner-dashboard'))
        self.assertEqual(product.product_name, 'Classic Sneakers')
        self.assertEqual(product.description, 'Updated description')
        self.assertEqual(product.price, 95)
        self.assertEqual(product.stock, 7)
        self.assertTrue(product.is_available)
        self.assertEqual(product.images.name, 'photos/products/sneakers.jpg')

    @patch(
        'dashboard.forms.upload_product_image',
        return_value='supabase://products/new-sneakers.png',
    )
    @override_settings(
        SUPABASE_PROJECT_URL='https://shop-example.supabase.co',
        SUPABASE_STORAGE_BUCKET='product-images',
    )
    def test_staff_can_replace_product_image(self, upload_image):
        user = self.create_staff_user()
        category = Category.objects.create(category_name='Shoes', slug='shoes')
        product = Product.objects.create(
            product_name='Everyday Sneakers',
            slug='everyday-sneakers',
            price=80,
            stock=4,
            category=category,
            images='photos/products/old-sneakers.jpg',
        )
        self.client.force_login(user)
        image_buffer = BytesIO()
        Image.new('RGB', (1, 1), color='white').save(image_buffer, format='PNG')
        image = SimpleUploadedFile(
            'new-sneakers.png', image_buffer.getvalue(), content_type='image/png'
        )

        response = self.client.post(
            reverse('owner-product-edit', args=[product.pk]),
            {
                'product_name': product.product_name,
                'description': '',
                'price': '80',
                'stock': '4',
                'category': str(category.pk),
                'is_available': 'on',
                'images': image,
            },
        )

        product.refresh_from_db()
        self.assertRedirects(response, reverse('owner-dashboard'))
        self.assertTrue(product.images.name.endswith('new-sneakers.png'))
        upload_image.assert_called_once()

    @patch('dashboard.forms.upload_product_image', return_value='supabase://products/new-dress.png')
    @override_settings(
        SUPABASE_PROJECT_URL='https://shop-example.supabase.co',
        SUPABASE_STORAGE_BUCKET='product-images',
    )
    def test_staff_can_add_product_with_uploaded_image(self, upload_image):
        user = self.create_staff_user()
        category = Category.objects.create(category_name='Clothing', slug='clothing')
        self.client.force_login(user)
        image_buffer = BytesIO()
        Image.new('RGB', (1, 1), color='white').save(image_buffer, format='PNG')
        image = SimpleUploadedFile(
            'new-dress.png', image_buffer.getvalue(), content_type='image/png'
        )

        response = self.client.post(
            reverse('owner-product-add'),
            {
                'product_name': 'Summer Dress',
                'description': 'A light summer dress',
                'price': '120',
                'stock': '5',
                'category': str(category.pk),
                'is_available': 'on',
                'images': image,
            },
        )

        product = Product.objects.get(product_name='Summer Dress')
        self.assertRedirects(response, reverse('owner-dashboard'))
        self.assertEqual(product.slug, 'summer-dress')
        self.assertEqual(product.stock, 5)
        self.assertEqual(product.images.name, 'supabase://products/new-dress.png')
        upload_image.assert_called_once()

    def test_product_edit_rejects_negative_price(self):
        user = self.create_staff_user()
        category = Category.objects.create(category_name='Shoes', slug='shoes')
        product = Product.objects.create(
            product_name='Everyday Sneakers',
            slug='everyday-sneakers',
            price=80,
            stock=4,
            category=category,
            images='photos/products/sneakers.jpg',
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse('owner-product-edit', args=[product.pk]),
            {
                'product_name': 'Everyday Sneakers',
                'description': '',
                'price': '-1',
                'stock': '4',
                'category': str(category.pk),
            },
        )

        product.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ensure this value is greater than or equal to 0')
        self.assertEqual(product.price, 80)

    def test_staff_can_update_placed_order_status(self):
        user = self.create_staff_user()
        order = self.create_placed_order(user)
        self.client.force_login(user)

        response = self.client.post(
            reverse('owner-order-status', args=[order.pk]),
            {'status': 'Accepted'},
        )

        order.refresh_from_db()
        self.assertRedirects(response, reverse('owner-dashboard'))
        self.assertEqual(order.status, 'Accepted')

    def test_order_status_rejects_invalid_values(self):
        user = self.create_staff_user()
        order = self.create_placed_order(user)
        self.client.force_login(user)

        response = self.client.post(
            reverse('owner-order-status', args=[order.pk]),
            {'status': 'Shipped'},
        )

        order.refresh_from_db()
        self.assertRedirects(response, reverse('owner-dashboard'))
        self.assertEqual(order.status, 'New')

    def test_order_status_updates_require_post(self):
        user = self.create_staff_user()
        order = self.create_placed_order(user)
        self.client.force_login(user)

        response = self.client.get(reverse('owner-order-status', args=[order.pk]))

        self.assertEqual(response.status_code, 405)
        order.refresh_from_db()
        self.assertEqual(order.status, 'New')

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

    def create_staff_user(self):
        user = get_user_model().objects.create_user(
            first_name='Shop',
            last_name='Owner',
            username='shopowner',
            email='owner@example.com',
            password='test-password-123',
        )
        user.is_staff = True
        user.save(update_fields=['is_staff'])
        return user

    def create_placed_order(self, user):
        return Order.objects.create(
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


class ProductMediaStorageTests(TestCase):
    @override_settings(
        SUPABASE_PROJECT_URL='https://shop-example.supabase.co',
        SUPABASE_STORAGE_BUCKET='product-images',
    )
    def test_supabase_product_image_uses_public_storage_url(self):
        from .storage import HybridProductMediaStorage

        storage = HybridProductMediaStorage()

        self.assertEqual(
            storage.url('supabase://products/red-dress.png'),
            'https://shop-example.supabase.co/storage/v1/object/public/'
            'product-images/products/red-dress.png',
        )
