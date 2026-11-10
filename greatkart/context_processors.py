from django.conf import settings


def seo_metadata(request):
    return {
        'canonical_url': f'{settings.SEO_SITE_URL}{request.path}',
    }
