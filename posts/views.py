# posts/views.py
from rest_framework import generics, permissions
from .models import Post
from .serializers import PostListSerializer, PostCreateSerializer, PostUpdateSerializer
from .permissions import IsOwnerOrReadOnly
from rest_framework.pagination import PageNumberPagination
from rest_framework.generics import CreateAPIView

import logging
logger = logging.getLogger(__name__)

class PostCreateView(CreateAPIView):
    def create(self, request, *args, **kwargs):
        logger.info(f"Auth header: {request.headers.get('Authorization')}")
        logger.info(f"User: {request.user}")
        logger.info(f"Data: {request.data}")
        return super().create(request, *args, **kwargs)




class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50

class PostListCreateView(generics.ListCreateAPIView):
    queryset = Post.objects.filter(is_active=True).select_related('author')
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = StandardResultsSetPagination

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PostCreateSerializer
        return PostListSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

class PostRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Post.objects.all().select_related('author')
    permission_classes = [IsOwnerOrReadOnly]
    lookup_field = 'id'

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return PostUpdateSerializer
        return PostListSerializer
