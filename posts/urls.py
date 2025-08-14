# posts/urls.py
from django.urls import path
from .views import PostListCreateView, PostRetrieveUpdateDestroyView

urlpatterns = [
    path('', PostListCreateView.as_view(), name='post-list-create'),            # POST /api/posts/  GET /api/posts/
    path('<int:id>/', PostRetrieveUpdateDestroyView.as_view(), name='post-detail'), # GET/PUT/PATCH/DELETE /api/posts/{id}/
]
