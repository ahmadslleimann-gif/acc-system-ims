from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CashBankAccountViewSet, CashTransactionViewSet

router = DefaultRouter()
router.register("accounts", CashBankAccountViewSet, basename="cashbankaccount")
router.register("transactions", CashTransactionViewSet, basename="cashtransaction")

urlpatterns = [path("", include(router.urls))]
