from .views import _get_cart_count

def counter(request):
    if 'admin' in request.path:
        return {}
    return {'cart_count': _get_cart_count(request)}
