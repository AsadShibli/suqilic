import csv

from django.db import transaction
from django.http import HttpResponse
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .permissions import IsStaff


class IdListSerializer(serializers.Serializer):
    ids = serializers.ListField(child=serializers.IntegerField(min_value=1), allow_empty=False)


class BulkDeleteMixin:
    @action(detail=False, methods=["post"], url_path="bulk-delete")
    def bulk_delete(self, request):
        s = IdListSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        deleted, _ = self.get_queryset().filter(id__in=s.validated_data["ids"]).delete()
        return Response({"deleted": deleted})


class ReorderMixin:
    """POST {ids: [...]} → sets `position` to the index of each id."""

    position_field = "position"

    @action(detail=False, methods=["post"])
    def reorder(self, request):
        s = IdListSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        ids = s.validated_data["ids"]
        objs = {o.id: o for o in self.get_queryset().filter(id__in=ids)}
        with transaction.atomic():
            for index, obj_id in enumerate(ids):
                if obj := objs.get(obj_id):
                    setattr(obj, self.position_field, index)
            self.get_queryset().model.objects.bulk_update(objs.values(), [self.position_field])
        return Response(status=status.HTTP_204_NO_CONTENT)


class CsvExportMixin:
    """Subclasses define `csv_fields` as [(header, attribute_or_callable), ...]."""

    csv_fields: list = []
    csv_filename = "export.csv"

    @action(detail=False, methods=["get"])
    def export(self, request):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{self.csv_filename}"'
        writer = csv.writer(response)
        writer.writerow([h for h, _ in self.csv_fields])
        for obj in self.filter_queryset(self.get_queryset()).iterator(chunk_size=500):
            writer.writerow([f(obj) if callable(f) else getattr(obj, f) for _, f in self.csv_fields])
        return response


class AdminModelViewSet(BulkDeleteMixin, viewsets.ModelViewSet):
    """Staff-only CRUD with bulk delete. Subclasses set queryset/serializer and filter fields."""

    permission_classes = [IsStaff]
