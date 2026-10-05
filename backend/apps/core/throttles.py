from rest_framework.throttling import SimpleRateThrottle


class IPScopedThrottle(SimpleRateThrottle):
    """Rate-limit by client IP (authenticated or not) using `scope` from DEFAULT_THROTTLE_RATES."""

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": self.get_ident(request)}


class AuthThrottle(IPScopedThrottle):
    scope = "auth"


class AdminLoginThrottle(IPScopedThrottle):
    scope = "admin_login"


class OrderThrottle(IPScopedThrottle):
    scope = "orders"


class FormThrottle(IPScopedThrottle):
    scope = "forms"


class TrackThrottle(IPScopedThrottle):
    scope = "track"


class PaymentThrottle(IPScopedThrottle):
    scope = "payments"
