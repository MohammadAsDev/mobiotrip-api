from rest_framework import generics
from rest_framework.response import Response

from .permissions import IsStaffOrPostOwner, IsPublisher
from .models import Post, PostTag
from .serializers import *

# Create your views here.

"""
    Tag-related view
"""
class PostTagsView(generics.ListCreateAPIView):
    serializer_class = TagSerializer
    permission_classes = [IsPublisher, ]
    queryset = PostTag.objects.all()


class TagDetailsView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TagSerializer
    permission_classes = [IsPublisher, ]
    queryset = PostTag.objects.all()

"""
    Post-related view
"""
class CreatePostView(generics.CreateAPIView):
    serializer_class = PostSerializer
    permission_classes = [IsPublisher, ]
    queryset = Post.objects.all()

class ListPostViews(generics.ListAPIView):
    serializer_class = PostModelSerializer
    permission_classes = [IsStaffOrPostOwner, ]
    queryset = Post.objects.all()

    def get_queryset(self):
        queryset = self.queryset
        if not self.request.user.is_staff:
            queryset = self.get_owned_posts(self.request.user)

        return queryset

    def get_owned_posts(self, user):
        return Post.objects.filter(publisher = user)


class UpdatePostView(generics.UpdateAPIView):
    serializer_class = PostSerializer
    permission_classes = [IsStaffOrPostOwner, ]
    queryset = Post.objects.all()

class PostDetailsView(generics.RetrieveDestroyAPIView):
    serializer_class = PostModelSerializer
    permission_classes = [IsStaffOrPostOwner, ]
    queryset = Post.objects.all()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        tags_id = serializer.data.get("tags")
        
        tags_data = TagSerializer(PostTag.objects.filter(id__in=tags_id) , many =True).data

        response = {
            "post_title" : serializer.data.get("title"),
            "post_content" : serializer.data.get("content"), 
            "tags" : tags_data
        }
        return Response(response)