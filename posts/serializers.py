# posts/serializers.py
from rest_framework import serializers
from .models import Post
from django.utils import timezone
import uuid
from .supabase_utils import upload_image_to_supabase

class PostListSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source='author.username', read_only=True)

    class Meta:
        model = Post
        fields = ('id', 'content', 'author', 'author_username', 'image_url',
                  'category', 'is_active', 'like_count', 'comment_count',
                  'created_at', 'updated_at')
        read_only_fields = ('author', 'like_count', 'comment_count', 'created_at', 'updated_at')

class PostCreateSerializer(serializers.ModelSerializer):
    image_file = serializers.ImageField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Post
        fields = ('id', 'content', 'image_file', 'image_url', 'category')
        read_only_fields = ('id', 'image_url')

    def validate_content(self, value):
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError('Content cannot be empty.')
        if len(value) > 280:
            raise serializers.ValidationError('Content max length is 280 characters.')
        return value.strip()

    def validate_category(self, value):
        allowed = [choice[0] for choice in Post.CATEGORY_CHOICES]
        if value not in allowed:
            raise serializers.ValidationError('Invalid category.')
        return value

    def validate_image_file(self, value):
        # image validation already in supabase_utils, but validation here gives earlier feedback
        max_size = 2 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError('Image too large. Max 2MB.')
        allowed = ('image/jpeg', 'image/png')
        if value.content_type not in allowed:
            raise serializers.ValidationError('Unsupported file type. Allowed: JPEG, PNG.')
        return value

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user
        image_file = validated_data.pop('image_file', None)
        # create post first without image
        post = Post.objects.create(author=user, **validated_data)
        # if image exists, upload and set image_url
        if image_file:
            ext = 'jpg' if image_file.content_type == 'image/jpeg' else 'png'
            dest_path = f'posts/{user.id}/post_{post.id}_{uuid.uuid4().hex}.{ext}'
            public_url = upload_image_to_supabase(image_file, dest_path)
            post.image_url = public_url
            post.save()
        return post

class PostUpdateSerializer(serializers.ModelSerializer):
    image_file = serializers.ImageField(write_only=True, required=False, allow_null=True)
    remove_image = serializers.BooleanField(write_only=True, required=False, default=False)

    class Meta:
        model = Post
        fields = ('content', 'image_file', 'remove_image', 'category', 'is_active')

    def validate_content(self, value):
        if value is not None and len(value) > 280:
            raise serializers.ValidationError('Content max length is 280 characters.')
        return value

    def validate_image_file(self, value):
        max_size = 2 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError('Image too large. Max 2MB.')
        allowed = ('image/jpeg', 'image/png')
        if value.content_type not in allowed:
            raise serializers.ValidationError('Unsupported file type. Allowed: JPEG, PNG.')
        return value

    def update(self, instance, validated_data):
        image_file = validated_data.pop('image_file', None)
        remove_image = validated_data.pop('remove_image', False)
        for attr, val in validated_data.items():
            setattr(instance, attr, val if val is not None else getattr(instance, attr))
        # handle image
        if remove_image:
            instance.image_url = None
        if image_file:
            import uuid
            ext = 'jpg' if image_file.content_type == 'image/jpeg' else 'png'
            dest_path = f'posts/{instance.author.id}/post_{instance.id}_{uuid.uuid4().hex}.{ext}'
            public_url = upload_image_to_supabase(image_file, dest_path)
            instance.image_url = public_url
        instance.save()
        return instance
