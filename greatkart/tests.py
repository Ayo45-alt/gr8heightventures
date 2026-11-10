from xml.etree import ElementTree

from django.test import TestCase
from django.urls import reverse

from category.models import Category
from store.models import Product


class SearchEngineDiscoveryTests(TestCase):
    def test_robots_txt_allows_public_pages_and_references_sitemap(self):
        response = self.client.get(reverse('robots-txt'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Allow: /')
        self.assertContains(response, 'Disallow: /owner/')
        self.assertContains(
            response,
            'Sitemap: https://www.kemisshop.com.ng/sitemap.xml',
        )

    def test_sitemap_contains_public_pages_and_available_products(self):
        category = Category.objects.create(
            category_name='Shoes',
            slug='shoes',
        )
        Product.objects.create(
            product_name='Everyday Shoes',
            slug='everyday-shoes',
            description='Comfortable shoes',
            price=50000,
            stock=2,
            category=category,
            images='photos/products/shoes.jpg',
            is_available=True,
        )
        Product.objects.create(
            product_name='Hidden Shoes',
            slug='hidden-shoes',
            description='Unavailable shoes',
            price=40000,
            stock=2,
            category=category,
            images='photos/products/hidden.jpg',
            is_available=False,
        )

        response = self.client.get(reverse('sitemap'))
        xml = ElementTree.fromstring(response.content)
        namespace = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        urls = [
            node.text
            for node in xml.findall('sm:url/sm:loc', namespace)
        ]

        self.assertEqual(response.status_code, 200)
        self.assertIn('https://www.kemisshop.com.ng/', urls)
        self.assertIn('https://www.kemisshop.com.ng/store/', urls)
        self.assertIn(
            'https://www.kemisshop.com.ng/store/category/shoes/everyday-shoes/',
            urls,
        )
        self.assertNotIn(
            'https://www.kemisshop.com.ng/store/category/shoes/hidden-shoes/',
            urls,
        )

    def test_homepage_has_canonical_and_search_description(self):
        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            '<link rel="canonical" href="https://www.kemisshop.com.ng/">',
            html=True,
        )
        self.assertContains(response, 'name="description"')
        self.assertContains(
            response,
            "<title>Kemi's Shop Nigeria | Women's Clothes, Dresses",
        )
