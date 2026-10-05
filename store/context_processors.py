from .models import Wishlist

def _get_session_key(request):
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key

def wishlist_info(request):
    if 'admin' in request.path:
        return {}
    
    wishlist_count = 0
    wishlist_ids = set()
    try:
        if request.user.is_authenticated:
            items = Wishlist.objects.filter(user=request.user)
        else:
            session_key = _get_session_key(request)
            items = Wishlist.objects.filter(session_id=session_key)
        
        wishlist_count = items.count()
        wishlist_ids = set(items.values_list('product_id', flat=True))
    except Exception:
        wishlist_count = 0
        wishlist_ids = set()

    return {
        'wishlist_count': wishlist_count,
        'wishlist_product_ids': wishlist_ids,
    }
