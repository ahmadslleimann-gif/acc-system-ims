from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.common.permissions import HasModelPermission
from apps.accounting_engine.services import PostingService
from .models import JournalEntry
from .serializers import JournalEntrySerializer


class JournalEntryViewSet(viewsets.ModelViewSet):
    queryset = JournalEntry.objects.prefetch_related("lines__account").all()
    serializer_class = JournalEntrySerializer
    permission_classes = [IsAuthenticated, HasModelPermission]
    filterset_fields = ["status", "entry_date", "source_type"]
    search_fields = ["entry_no", "memo", "source_id"]
    required_perms = {
        "POST": ["journal.add_journalentry"],
        "PUT": ["journal.change_journalentry"],
        "PATCH": ["journal.change_journalentry"],
        "DELETE": ["journal.delete_journalentry"],
    }

    def destroy(self, request, *args, **kwargs):
        entry = self.get_object()
        if entry.status != JournalEntry.Status.DRAFT:
            return Response({"detail": "Only DRAFT entries can be deleted."}, status=400)
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=["post"])
    def post_entry(self, request, pk=None):
        entry = self.get_object()
        PostingService.post_draft(entry, user=request.user)
        return Response(self.get_serializer(entry).data)

    @action(detail=True, methods=["post"])
    def reverse(self, request, pk=None):
        entry = self.get_object()
        reversal = PostingService.reverse(
            entry, user=request.user,
            date=request.data.get("date") or None,
            memo=request.data.get("memo"),
        )
        return Response(self.get_serializer(reversal).data, status=201)
