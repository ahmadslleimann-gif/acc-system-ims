from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ExpenseCategoryViewSet, ExpenseViewSet

router = DefaultRouter()
router.register("categories", ExpenseCategoryViewSet, basename="expensecategory")
router.register("", ExpenseViewSet, basename="expense")

urlpatterns = [path("", include(router.urls))]
