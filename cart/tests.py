from django.test import TestCase
from django.urls import reverse
from urllib.parse import parse_qs, urlparse

from category.models import Category
from store.models import Product
from cart.models import Cart, CartItem


class AddCartAjaxTests(TestCase):
    def setUp(self):
        category = Category.objects.create(category_name='Dresses', slug='dresses')
        self.product = Product.objects.create(
            product_name='Test dress',
            slug='test-dress',
            price=10000,
            stock=2,
            images='test-dress.jpg',
            category=category,
        )
        self.add_url = reverse('add_cart', args=[self.product.id])

    def add_product(self):
        return self.client.post(
            self.add_url,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

    def test_product_detail_form_fallback_returns_to_product(self):
        response = self.client.post(
            self.add_url,
            {'stay_on_product_page': '1'},
            follow=True,
        )

        self.assertRedirects(response, self.product.get_url())
        self.assertEqual(CartItem.objects.get(product=self.product).quantity, 1)
        self.assertContains(response, "showBagToast('Added to Bag')")
        self.assertEqual(
            [str(message) for message in response.context['messages']],
            ['Added to Bag'],
        )

    def test_cart_quantity_form_still_returns_to_cart(self):
        response = self.client.post(self.add_url)

        self.assertRedirects(response, reverse('cart'))

    def test_ajax_add_stays_on_page_and_updates_cart_count(self):
        response = self.add_product()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'ok', 'cart_count': 1})
        self.assertEqual(CartItem.objects.get(product=self.product).quantity, 1)
        cart_page = self.client.get(reverse('cart'))
        self.assertEqual(cart_page.context['cart_count'], 1)

    def test_ajax_add_reports_stock_limit_without_changing_cart(self):
        self.add_product()
        self.add_product()

        response = self.add_product()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['status'], 'error')
        self.assertEqual(CartItem.objects.get(product=self.product).quantity, 2)

    def test_empty_guest_cart_count_is_zero(self):
        self.assertEqual(Cart.objects.count(), 0)
        response = self.client.get(reverse('cart'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['cart_count'], 0)

    def test_whatsapp_order_includes_name_address_and_cart_contents(self):
        self.add_product()

        response = self.client.post(
            reverse('order_whatsapp'),
            {
                'customer_name': 'Ada Lovelace',
                'delivery_address': '12 Market Road, Lagos',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(urlparse(response['Location']).netloc, 'wa.me')
        message = parse_qs(urlparse(response['Location']).query)['text'][0]
        self.assertIn('Name: Ada Lovelace', message)
        self.assertIn('Delivery address: 12 Market Road, Lagos', message)
        self.assertIn('Test dress x1 - ₦10,000', message)
        self.assertIn('Subtotal: ₦10,000', message)

    def test_whatsapp_order_requires_name_and_delivery_address(self):
        self.add_product()

        response = self.client.post(
            reverse('order_whatsapp'),
            {'customer_name': 'Ada Lovelace', 'delivery_address': '   '},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please enter your name and delivery address to continue.')

    def test_whatsapp_order_rejects_empty_cart(self):
        response = self.client.post(
            reverse('order_whatsapp'),
            {'customer_name': 'Ada Lovelace', 'delivery_address': '12 Market Road, Lagos'},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Your Bag is empty. Add an item before placing an order.')
