from rest_framework import serializers

from .models import Post, PostTag

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostTag
        fields = "__all__"

class PostSerializer(serializers.ModelSerializer):
    tags = serializers.ListField(
        child = serializers.CharField(allow_blank=False, max_length=50, trim_whitespace=True)
    )
    
    class Meta:
        model = Post
        fields = ['id' , 'title' , 'content' , 'tags']

    def validate_tags(self, value):
        tag_ids = []
        for tag_name in value:
            tag_name = tag_name.lower()
            try:
                tag = PostTag.objects.get(tag_name=tag_name)
                tag_ids.append(tag.id)
            except PostTag.DoesNotExist:
                new_tag = PostTag()
                new_tag.tag_name = tag_name
                new_tag.description = "newly created tag"
                new_tag.save()
                tag_ids.append(new_tag.id)
                # raise serializers.ValidationError(f"Tag with ID {tag_id} does not exist.")
        return tag_ids


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

    tags = TagSerializer(many=True, read_only=True)
