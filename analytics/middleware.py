from django.db import connection
from django.utils import timezone

from .models import DailyPageView


class PageViewCounterMiddleware:
    excluded_prefixes = ('/admin/', '/owner/', '/static/', '/media/')

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if self._should_count(request, response):
            table = connection.ops.quote_name(DailyPageView._meta.db_table)
            day_column = connection.ops.quote_name(
                DailyPageView._meta.get_field('day').column
            )
            views_column = connection.ops.quote_name(
                DailyPageView._meta.get_field('views').column
            )
            with connection.cursor() as cursor:
                cursor.execute(
                    f'INSERT INTO {table} ({day_column}, {views_column}) '
                    f'VALUES (%s, 1) '
                    f'ON CONFLICT ({day_column}) DO UPDATE SET '
                    f'{views_column} = {table}.{views_column} + 1',
                    [timezone.localdate()],
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
