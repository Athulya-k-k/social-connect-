from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from .models import Follow, Like, Comment
from .serializers import FollowSerializer, FollowerListSerializer, LikeSerializer, CommentSerializer
from posts.models import Post
from django.core.paginator import Paginator
from django.db.models import Count, Exists, OuterRef
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Follow, Like, Comment
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Notification
from .serializers import NotificationSerializer


User = get_user_model()


# ---------- FOLLOW SYSTEM ----------
class FollowUserView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = FollowSerializer

    def post(self, request, user_id):
        following = get_object_or_404(User, id=user_id)
        if Follow.objects.filter(follower=request.user, following=following).exists():
            return Response({"detail": "Already following"}, status=status.HTTP_400_BAD_REQUEST)
        Follow.objects.create(follower=request.user, following=following)
        return Response({"detail": f"You are now following {following.username}"})


class UnfollowUserView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, user_id):
        following = get_object_or_404(User, id=user_id)
        follow_instance = Follow.objects.filter(follower=request.user, following=following)
        if not follow_instance.exists():
            return Response({"detail": "You are not following this user"}, status=status.HTTP_400_BAD_REQUEST)
        follow_instance.delete()
        return Response({"detail": "Unfollowed successfully"})


class UserFollowersView(generics.ListAPIView):
    serializer_class = FollowerListSerializer

    def get_queryset(self):
        user = get_object_or_404(User, id=self.kwargs['user_id'])
        return User.objects.filter(following_set__following=user)


class UserFollowingView(generics.ListAPIView):
    serializer_class = FollowerListSerializer

    def get_queryset(self):
        user = get_object_or_404(User, id=self.kwargs['user_id'])
        return User.objects.filter(followers_set__follower=user)


# ---------- LIKE SYSTEM ----------
class LikePostView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        if Like.objects.filter(user=request.user, post=post).exists():
            return Response({'detail': 'Already liked'}, status=status.HTTP_400_BAD_REQUEST)
        Like.objects.create(user=request.user, post=post)
        return Response({'detail': 'Post liked'})


class UnlikePostView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        like = get_object_or_404(Like, user=request.user, post=post)
        like.delete()
        return Response({'detail': 'Post unliked'})


class LikeStatusView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        liked = Like.objects.filter(user=request.user, post=post).exists()
        return Response({"liked": liked})


# ---------- COMMENT SYSTEM ----------
class AddCommentView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CommentSerializer
    
    def perform_create(self, serializer):
        post = get_object_or_404(Post, id=self.kwargs['post_id'])
        serializer.save(author=self.request.user, post=post)


class GetCommentsView(generics.ListAPIView):
    serializer_class = CommentSerializer

    def get_queryset(self):
        post = get_object_or_404(Post, id=self.kwargs['post_id'])
        return Comment.objects.filter(post=post, is_active=True)


class DeleteOwnCommentView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, comment_id):
        comment = get_object_or_404(Comment, id=comment_id, author=request.user)
        comment.delete()
        return Response({"detail": "Comment deleted"})



# social/views.py
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def feed(request):
    """
    Returns the chronological feed of posts from followed users
    """
    user = request.user
    
    # Get IDs of followed users
    following_ids = Follow.objects.filter(follower=user).values_list('following_id', flat=True)
    
    # Get posts from followed users
    posts_qs = Post.objects.filter(
        author_id__in=list(following_ids),
        is_active=True
    ).annotate(
        like_count_actual=Count('likes', distinct=True),
        comment_count_actual=Count('comments', distinct=True),
        is_liked=Exists(Like.objects.filter(post=OuterRef('pk'), user=user))
    ).order_by('-created_at')
    
    # Pagination
    page_number = request.GET.get('page', 1)
    paginator = Paginator(posts_qs, 20)
    page_obj = paginator.get_page(page_number)
    
    # Serialize response
    feed_data = []
    for post in page_obj:
        feed_data.append({
            "id": post.id,
            "content": post.content,
            "image_url": post.image_url,
            "category": post.category,
            "created_at": post.created_at.isoformat(),
            "author": {
                "id": post.author.id,
                "username": post.author.username,
                "first_name": post.author.first_name,
                "last_name": post.author.last_name,
            },
            "like_count": post.like_count_actual,
            "comment_count": post.comment_count_actual,
            "is_liked": post.is_liked,
        })

    return Response({
        "page": page_obj.number,
        "total_pages": paginator.num_pages,
        "has_next": page_obj.has_next(),
        "has_previous": page_obj.has_previous(),
        "results": feed_data
    })



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_notifications(request):
    notifications = Notification.objects.filter(recipient=request.user)
    serializer = NotificationSerializer(notifications, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_notification_as_read(request, notification_id):
    try:
        notification = Notification.objects.get(id=notification_id, recipient=request.user)
        notification.is_read = True
        notification.save()
        return Response({"message": "Notification marked as read"})
    except Notification.DoesNotExist:
        return Response({"error": "Notification not found"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_all_notifications_as_read(request):
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return Response({"message": "All notifications marked as read"})