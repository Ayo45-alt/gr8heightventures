from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from category.models import Category
from .models import Product, Variation


class StoreCategoryPerformanceTests(TestCase):
    def test_category_page_paginates_and_prefetches_size_variations(self):
        category = Category.objects.create(
            category_name='Shoes',
            slug='shoes',
        )
        products = Product.objects.bulk_create([
            Product(
                product_name=f'Shoe {index}',
                slug=f'shoe-{index}',
                price=100,
                stock=5,
                category=category,
                images='photos/products/shoe.jpg',
            )
            for index in range(65)
        ])
        Variation.objects.bulk_create([
            Variation(
                product=product,
                variation_category='size',
                variation_value=size,
                is_active=True,
            )
            for product in products
            for size in ('38', '39')
        ])

        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(
                reverse('products_by_category', args=[category.slug])
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['product_count'], 65)
        self.assertEqual(len(response.context['products']), 60)
        variation_queries = [
            query for query in queries
            if 'store_variation' in query['sql'].lower()
        ]
        self.assertEqual(len(variation_queries), 1)
