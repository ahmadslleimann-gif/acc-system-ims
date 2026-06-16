from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import JournalEntryViewSet

router = DefaultRouter()
router.register("entries", JournalEntryViewSet, basename="journalentry")

urlpatterns = [path("", include(router.urls))]
