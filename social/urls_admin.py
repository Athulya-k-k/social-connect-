from django.urls import path
from . import views_admin

urlpatterns = [
    path('users/', views_admin.AdminUserListView.as_view()),
    path('users/<int:user_id>/', views_admin.AdminUserDetailView.as_view()),
    path('users/<int:user_id>/deactivate/', views_admin.AdminDeactivateUserView.as_view()),
    path('posts/', views_admin.AdminPostListView.as_view()),
    path('posts/<int:post_id>/', views_admin.AdminDeletePostView.as_view()),
    path('stats/', views_admin.AdminStatsView.as_view()),
]
