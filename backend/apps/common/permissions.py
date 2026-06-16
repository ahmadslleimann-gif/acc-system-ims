from rest_framework.permissions import BasePermission, SAFE_METHODS


class HasModelPermission(BasePermission):
    """
    Granular RBAC: maps DRF actions to Django model permissions.

    Set `required_perms` on the view as a dict, e.g.:
        required_perms = {
            "GET": ["journal.view_journalentry"],
            "POST": ["journal.add_journalentry"],
        }
    A user passes if they hold ALL listed permissions for the request method.
    Super Admins (is_superuser) always pass.
    """

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_superuser:
            return True
        required = getattr(view, "required_perms", {})
        perms = required.get(request.method, [])
        if not perms:
            # Default: read for any authenticated user, write requires explicit perms.
            return request.method in SAFE_METHODS
        return all(request.user.has_perm(p) for p in perms)


class ReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS
