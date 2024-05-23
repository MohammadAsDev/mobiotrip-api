from django.db import models
from employees_manager.models import Publisher

# Create your models here.

class PostTag(models.Model):
    name = models.CharField(name="tag_name" , blank=False, max_length=100 , unique=True)
    description = models.CharField(name="tag_description", blank=False, max_length=200)

class Post(models.Model):
    title = models.CharField(name="title", db_index=True , blank=False,  max_length=100)
    publisher = models.ForeignKey(to=Publisher, on_delete=models.SET_NULL, null=True, related_name="publisher")
    content = models.CharField(name="content" , blank=False, max_length=500)
    tags = models.ManyToManyField(to=PostTag , related_name="post_tags")
