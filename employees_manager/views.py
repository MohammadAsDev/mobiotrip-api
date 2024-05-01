from rest_framework.generics import ListAPIView , RetrieveUpdateDestroyAPIView , CreateAPIView
from rest_framework.permissions import IsAdminUser

from django_filters.rest_framework import DjangoFilterBackend

from users_manager.permissions import IsOwnerOrStaff
from .serializers import PublisherSerializer
from .models import Publisher
# Create your views here.

class PublishersView(ListAPIView):
    permission_classes = [IsAdminUser]
    queryset = Publisher.objects.all()
    serializer_class = PublisherSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["username"]

    def get_queryset(self):
        email = self.request.query_params.get("email" , "")
        if email:
            selected_user_queyset = Publisher.objects.filter(username= email)
            return selected_user_queyset
        return super().get_queryset()

class CreatePublisher(CreateAPIView):
    permission_classes = [IsAdminUser]
    queryset = Publisher.objects.all()
    serializer_class = PublisherSerializer

class PublisherDetails(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsOwnerOrStaff]
    queryset = Publisher.objects.all()
    serializer_class = PublisherSerializer

