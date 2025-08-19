from django.contrib import admin
from .models import Post

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'content_preview', 'category', 'created_at', 'is_active', 'like_count', 'comment_count')
    list_filter = ('category', 'is_active', 'created_at')
    search_fields = ('content', 'author__username')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

    def content_preview(self, obj):
        return obj.content[:50] + ("..." if len(obj.content) > 50 else "")
    content_preview.short_description = "Content"

