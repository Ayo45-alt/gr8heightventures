from django.db.models import F
from django.utils import timezone

from .models import DailyPageView


class PageViewCounterMiddleware:
    excluded_prefixes = ('/admin/', '/owner/', '/static/', '/media/')

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if self._should_count(request, response):
            daily_views, _ = DailyPageView.objects.get_or_create(
                day=timezone.localdate()
            )
            DailyPageView.objects.filter(pk=daily_views.pk).update(
                views=F('views') + 1
            )

        return response

    def _should_count(self, request, response):
        accept = request.headers.get('Accept', '').lower()
        return (
            request.method == 'GET'
            and response.status_code == 200
            and 'text/html' in accept
            and not request.path.startswith(self.excluded_prefixes)
        )
