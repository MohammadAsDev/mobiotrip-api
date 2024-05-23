from rest_framework import serializers

from .models import Post, PostTag

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostTag
        fields = "__all__"

class PostSerializer(serializers.ModelSerializer):
    tags = serializers.ListField(
        child = serializers.IntegerField()
    )
    
    class Meta:
        model = Post
        fields = ['id' , 'title' , 'content' , 'tags']

    def validate_tags(self, value):
        for tag_id in value:
            try:
                PostTag.objects.get(id=tag_id)
            except PostTag.DoesNotExist:
                raise serializers.ValidationError(f"Tag with ID {tag_id} does not exist.")
        return value


    def create(self, validated_data):
        request = self.context.get("request")
        current_publisher = request.user
        post_tags = validated_data.pop("tags" , [])

        new_post = Post.objects.create(publisher = current_publisher , **validated_data)
        new_post.tags.set(post_tags)
        
        return {
            "title" : new_post.title, 
            "content" : new_post.content,
            "tags" : [int(tag.id) for tag in new_post.tags.all()]
        }
    
    def update(self, instance, validated_data):
        tags = validated_data.pop("tags" , [])

        for attr, val in validated_data.items():
            setattr(instance, attr ,val)

        instance.save()
        instance.tags.set(tags)

        return {
            "title" : instance.title, 
            "content" : instance.content,
            "tags" : [int(tag.id) for tag in instance.tags.all()]
        }
  


class PostModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = "__all__"
