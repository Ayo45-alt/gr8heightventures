from xml.etree import ElementTree

from django.conf import settings
from django.http import HttpResponse
from django.urls import reverse
from django.utils import timezone

from category.models import Category
from store.models import Product


SITEMAP_NAMESPACE = 'http://www.sitemaps.org/schemas/sitemap/0.9'


def robots_txt(request):
    content = '\n'.join((
        'User-agent: *',
        'Allow: /',
        'Disallow: /admin/',
        'Disallow: /owner/',
        'Disallow: /accounts/',
        'Disallow: /cart/',
        'Disallow: /orders/',
        f'Sitemap: {settings.SEO_SITE_URL}/sitemap.xml',
        '',
    ))
    return HttpResponse(content, content_type='text/plain')


def sitemap_xml(request):
    root = ElementTree.Element(
        f'{{{SITEMAP_NAMESPACE}}}urlset'
    )
    paths = {
        reverse('home'),
        reverse('store'),
        reverse('about'),
        reverse('contact'),
        reverse('delivery'),
        reverse('returns'),
        reverse('faqs'),
        reverse('privacy'),
        reverse('terms'),
    }
    paths.update(
        category.get_url()
        for category in Category.objects.order_by('slug')
    )

    products = (
        Product.objects.filter(is_available=True, stock__gt=0)
        .select_related('category')
        .order_by('pk')
    )
    product_last_modified = {}
    for product in products:
        path = reverse(
            'product_detail',
            args=[product.category.slug, product.slug],
        )
        paths.add(path)
        product_last_modified[path] = product.modified_date

    for path in sorted(paths):
        url_element = ElementTree.SubElement(
            root,
            f'{{{SITEMAP_NAMESPACE}}}url',
        )
        ElementTree.SubElement(
            url_element,
            f'{{{SITEMAP_NAMESPACE}}}loc',
        ).text = f'{settings.SEO_SITE_URL}{path}'
        last_modified = product_last_modified.get(path)
        if last_modified:
            ElementTree.SubElement(
                url_element,
                f'{{{SITEMAP_NAMESPACE}}}lastmod',
            ).text = timezone.localtime(last_modified).date().isoformat()

    content = ElementTree.tostring(
        root,
        encoding='utf-8',
        xml_declaration=True,
    )
    return HttpResponse(content, content_type='application/xml; charset=utf-8')
