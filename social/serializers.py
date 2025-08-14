from rest_framework import serializers
from .models import Follow, Like, Comment
from django.contrib.auth import get_user_model
from .models import Notification
from rest_framework import serializers
from django.contrib.auth import get_user_model
from posts.models import Post

User = get_user_model()




class FollowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follow
        fields = ['follower', 'following', 'created_at']


class FollowerListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = ['user', 'post', 'created_at']


class CommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.username', read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'content', 'author', 'author_name', 'post', 'created_at', 'is_active']
        read_only_fields = ['author', 'created_at']


class NotificationSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source="sender.username", read_only=True)
    recipient_username = serializers.CharField(source="recipient.username", read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id', 'sender_username', 'recipient_username', 'notification_type',
            'post', 'message', 'is_read', 'created_at'
        ]


class AdminUserSerializer(serializers.ModelSerializer):
    posts_count = serializers.SerializerMethodField()
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'is_active', 'is_staff', 'date_joined', 'last_login',
            'posts_count', 'followers_count', 'following_count'
        ]
    
    def get_posts_count(self, obj):
        return Post.objects.filter(author=obj, is_active=True).count()
    
    def get_followers_count(self, obj):
        return obj.followers_set.count()
    
    def get_following_count(self, obj):
        return obj.following_set.count()
    


class AdminPostSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source='author.username', read_only=True)
    
    class Meta:
        model = Post
        fields = [
            'id', 'content', 'author', 'author_username', 
            'image_url', 'category', 'like_count', 'comment_count',
            'is_active', 'created_at', 'updated_at'
        ]

class StatsSerializer(serializers.Serializer):
    total_users = serializers.IntegerField()
    total_posts = serializers.IntegerField()
    active_today = serializers.IntegerField()