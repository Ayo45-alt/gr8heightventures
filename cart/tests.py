from django.test import TestCase
from django.urls import reverse

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
