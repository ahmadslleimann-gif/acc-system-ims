from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.users_auth.urls")),
    path("api/company/", include("apps.company.urls")),
    path("api/coa/", include("apps.accounts_coa.urls")),
    path("api/journal/", include("apps.journal.urls")),
    path("api/inventory/", include("apps.inventory.urls")),
    path("api/customers/", include("apps.customers.urls")),
    path("api/suppliers/", include("apps.suppliers.urls")),
    path("api/sales/", include("apps.sales.urls")),
    path("api/purchases/", include("apps.purchases.urls")),
    path("api/cashbanks/", include("apps.cashbanks.urls")),
    path("api/expenses/", include("apps.expenses.urls")),
    path("api/reports/", include("apps.reports.urls")),
    path("api/audit/", include("apps.audit.urls")),
    path("api/dashboard/", include("apps.dashboard.urls")),
    # API schema / docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
