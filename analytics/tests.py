from django.http import HttpResponse
from django.test import RequestFactory, TestCase
from django.utils import timezone

from .middleware import PageViewCounterMiddleware
from .models import DailyPageView


class PageViewCounterMiddlewareTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = PageViewCounterMiddleware(
            lambda request: HttpResponse('ok')
        )

    def request(self, path='/', method='get', accept='text/html'):
        request = getattr(self.factory, method)(path, HTTP_ACCEPT=accept)
        return self.middleware(request)

    def test_counts_successful_html_page_views_without_storing_request_data(self):
        self.request('/store/')

        record = DailyPageView.objects.get(day=timezone.localdate())
        self.assertEqual(record.views, 1)
        self.assertEqual(
            {field.name for field in DailyPageView._meta.fields},
            {'id', 'day', 'views'},
        )

    def test_does_not_count_non_page_requests_or_owner_pages(self):
        self.request('/static/css/site.css', accept='text/css')
        self.request('/owner/')
        self.request('/admin/')
        self.request('/store/', method='post')

        self.assertFalse(DailyPageView.objects.exists())
