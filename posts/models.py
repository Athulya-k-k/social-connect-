# posts/models.py - Updated Post Model
from django.db import models
from django.conf import settings

class Post(models.Model):
    CATEGORY_GENERAL = 'general'
    CATEGORY_ANNOUNCEMENT = 'announcement'
    CATEGORY_QUESTION = 'question'

    CATEGORY_CHOICES = [
        (CATEGORY_GENERAL, 'General'),
        (CATEGORY_ANNOUNCEMENT, 'Announcement'),
        (CATEGORY_QUESTION, 'Question'),
    ]

    # Fixed: content field instead of title/description
    content = models.TextField(max_length=280)  # Main content field as per requirements
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    image_url = models.URLField(blank=True, null=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default=CATEGORY_GENERAL)
    is_active = models.BooleanField(default=True)
    like_count = models.PositiveIntegerField(default=0)
    comment_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.author.username}: {self.content[:50]}'