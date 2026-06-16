from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CompanyProfileView, TaxRateViewSet, FiscalPeriodViewSet

router = DefaultRouter()
router.register("tax-rates", TaxRateViewSet, basename="taxrate")
router.register("fiscal-periods", FiscalPeriodViewSet, basename="fiscalperiod")

urlpatterns = [
    path("profile/", CompanyProfileView.as_view(), name="company_profile"),
    path("", include(router.urls)),
]
