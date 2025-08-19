from django.urls import path
from . import views

urlpatterns = [
    # Follow
    path('users/<int:user_id>/follow/', views.FollowUserView.as_view()),
    path('users/<int:user_id>/unfollow/', views.UnfollowUserView.as_view()),
    path('users/<int:user_id>/followers/', views.UserFollowersView.as_view()),
    path('users/<int:user_id>/following/', views.UserFollowingView.as_view()),

    # Likes
    path('posts/<int:post_id>/like/', views.LikePostView.as_view(), name='like-post'),
    path('posts/<int:post_id>/unlike/', views.UnlikePostView.as_view(), name='unlike-post'),
    path('posts/<int:post_id>/like-status/', views.LikeStatusView.as_view(), name='like-status'),

    # Comments
      path('posts/<int:post_id>/comments/', views.GetCommentsView.as_view(), name='get-comments'),
    path('posts/<int:post_id>/comments/add/', views.AddCommentView.as_view(), name='add-comment'),
    path('comments/<int:comment_id>/delete/', views.DeleteOwnCommentView.as_view(), name='delete-comment'),
    
    # Feed - Fixed URL pattern
    path('feed/', views.feed, name='feed'),

    # Notifications
    path('notifications/', views.get_notifications, name='get_notifications'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_as_read, name='mark_notification_as_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_as_read, name='mark_all_notifications_as_read'),
]