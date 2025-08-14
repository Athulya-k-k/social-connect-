from django.dispatch import receiver
from .models import Follow, Like, Comment, Notification
from supabase import create_client
import os
from django.db.models.signals import post_save, post_delete

@receiver(post_save, sender=Follow)
def create_follow_notification(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            recipient=instance.following,
            sender=instance.follower,
            notification_type='follow',
            message=f"{instance.follower.username} started following you"
        )

@receiver(post_save, sender=Like)
def create_like_notification(sender, instance, created, **kwargs):
    if created:
        # Update post like count
        post = instance.post
        post.like_count = post.likes.count()
        post.save()
        
        # Create notification (don't notify yourself)
        if instance.user != instance.post.author:
            Notification.objects.create(
                recipient=instance.post.author,
                sender=instance.user,
                notification_type='like',
                post=instance.post,
                message=f"{instance.user.username} liked your post"
            )


@receiver(post_delete, sender=Like)
def update_like_count_on_delete(sender, instance, **kwargs):
    # Update post like count when like is deleted
    post = instance.post
    post.like_count = post.likes.count()
    post.save()






@receiver(post_save, sender=Comment)
def create_comment_notification(sender, instance, created, **kwargs):
    if created:
        # Update post comment count
        post = instance.post
        post.comment_count = post.comments.filter(is_active=True).count()
        post.save()
        
        # Create notification (don't notify yourself)
        if instance.author != instance.post.author:
            Notification.objects.create(
                recipient=instance.post.author,
                sender=instance.author,
                notification_type='comment',
                post=instance.post,
                message=f"{instance.author.username} commented on your post"
            )


@receiver(post_delete, sender=Comment)
def update_comment_count_on_delete(sender, instance, **kwargs):
    # Update post comment count when comment is deleted
    post = instance.post
    post.comment_count = post.comments.filter(is_active=True).count()
    post.save()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)




def send_to_supabase(notification):
    supabase.table("notifications").insert({
        "recipient_id": notification.recipient.id,
        "sender_id": notification.sender.id,
        "notification_type": notification.notification_type,
        "post_id": notification.post.id if notification.post else None,
        "message": notification.message,
        "is_read": notification.is_read,
        "created_at": notification.created_at.isoformat()
    }).execute()



