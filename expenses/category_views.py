from django.db.models import Q
from django.db.models.deletion import ProtectedError
from rest_framework import generics, permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from .models import Category
from .serializers import CategorySerializer


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Category.objects.filter(Q(user__isnull=True) | Q(user=user))

    def perform_update(self, serializer):
        if serializer.instance.is_system:
            raise PermissionDenied('System categories cannot be modified.')
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.is_system:
            raise PermissionDenied('System categories cannot be deleted.')
        try:
            self.perform_destroy(instance)
        except ProtectedError:
            return Response(
                {'detail': 'Cannot delete category that is used by expenses.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)
