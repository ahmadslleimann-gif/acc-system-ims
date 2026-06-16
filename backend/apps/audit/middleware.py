import threading

_thread_locals = threading.local()


def get_current_user():
    return getattr(_thread_locals, "user", None)


def get_current_ip():
    return getattr(_thread_locals, "ip", None)


class CurrentUserMiddleware:
    """Stashes the request user + IP in thread-local storage for audit signals."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.user = getattr(request, "user", None)
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        _thread_locals.ip = xff.split(",")[0].strip() if xff else request.META.get("REMOTE_ADDR")
        try:
            return self.get_response(request)
        finally:
            _thread_locals.user = None
            _thread_locals.ip = None
