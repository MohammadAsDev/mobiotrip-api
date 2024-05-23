from django.urls import path
from .views import *

urlpatterns = [
    path("posts/create/" , view=CreatePostView.as_view() , name="create_posts"),
    path("posts/" , view=ListPostViews.as_view() , name="create_posts"),
    path("posts/<int:pk>/" , view=PostDetailsView.as_view() , name="post_details"),
    path("posts/<int:pk>/update/" , view=UpdatePostView.as_view() , name="post_details"),
    path("tags/" , view=PostTagsView.as_view() , name="create_list_tags"),
    path("tags/<int:pk>/" , view=TagDetailsView.as_view() , name="tag_details"),
]
