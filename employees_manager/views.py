from rest_framework import generics
from rest_framework.permissions import IsAdminUser
from rest_framework import views
from rest_framework.response import Response

from django_filters.rest_framework import DjangoFilterBackend

from users_manager.permissions import IsOwnerOrStaff
from users_manager.serializers import UserSerializer

from news_platform.permissions import IsPublisher
from news_platform.models import Post
from news_platform.serializers import PostSerializer, PostModelSerializer

from .serializers import PublisherSerializer
from .models import Publisher
# Create your views here.

class PublishersView(generics.ListAPIView):
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

class CreatePublisher(generics.CreateAPIView):
    permission_classes = [IsAdminUser]
    queryset = Publisher.objects.all()
    serializer_class = PublisherSerializer

class PublisherDetails(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsOwnerOrStaff]
    queryset = Publisher.objects.all()
    serializer_class = PublisherSerializer

class AccountDetails(views.APIView):
    def get(self, request, format=None):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

class PublisherPostsView(generics.ListAPIView):
    queryset = Post.objects.all()
    permission_classes = [IsPublisher, ]
    serializer_class = PostModelSerializer

    def get_queryset(self, user):
        return self.queryset.filter(publisher = user.id)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset(request.user))

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)