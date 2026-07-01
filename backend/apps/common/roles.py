"""Role helpers used for field-level and workflow security decisions."""


def in_group(user, name: str) -> bool:
    return bool(user and user.is_authenticated and user.groups.filter(name=name).exists())


def is_super_admin(user) -> bool:
    return bool(user and user.is_authenticated and (user.is_superuser or in_group(user, "Super Admin")))


def is_accountant(user) -> bool:
    return in_group(user, "Accountant")


def can_view_cost(user) -> bool:
    """Only Super Admin and Accountant may see cost prices / margins / valuation."""
    return is_super_admin(user) or is_accountant(user)
