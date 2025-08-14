from django.contrib.auth import get_user_model
from django.utils.timezone import now
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count
from datetime import date

from posts.models import Post
from .serializers import AdminUserSerializer, AdminPostSerializer, StatsSerializer
from .permissions import IsAdminUserCustom

User = get_user_model()

# 1. List All Users
class AdminUserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = AdminUserSerializer
    permission_classes = [IsAuthenticated, IsAdminUserCustom]

# 2. Get User Details
class AdminUserDetailView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = AdminUserSerializer
    permission_classes = [IsAuthenticated, IsAdminUserCustom]
    lookup_url_kwarg = 'user_id'

# 3. Deactivate User
class AdminDeactivateUserView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserCustom]

    def post(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            user.is_active = False
            user.save()
            return Response({"message": "User deactivated successfully."})
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

# 4. List All Posts
class AdminPostListView(generics.ListAPIView):
    queryset = Post.objects.all()
    serializer_class = AdminPostSerializer
    permission_classes = [IsAuthenticated, IsAdminUserCustom]

# 5. Delete Any Post
class AdminDeletePostView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserCustom]

    def delete(self, request, post_id):
        try:
            post = Post.objects.get(id=post_id)
            post.delete()
            return Response({"message": "Post deleted successfully."})
        except Post.DoesNotExist:
            return Response({"error": "Post not found."}, status=status.HTTP_404_NOT_FOUND)

# 6. Basic statistics
class AdminStatsView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserCustom]

    def get(self, request):
        total_users = User.objects.count()
        total_posts = Post.objects.count()
        active_today = User.objects.filter(last_login__date=date.today()).count()

        data = {
            "total_users": total_users,
            "total_posts": total_posts,
            "active_today": active_today
        }
        serializer = StatsSerializer(data)
        return Response(data)
