# accounts/views.py
from django.contrib.auth import get_user_model
from django.contrib.auth.models import update_last_login
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_str, smart_bytes
from django.core.mail import send_mail
from django.urls import reverse
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from .tokens import email_verification_token
from .serializers import (
    RegisterSerializer, EmailVerificationSerializer, LoginSerializer,
    ResetPasswordEmailRequestSerializer, SetNewPasswordSerializer,
    ChangePasswordSerializer, get_tokens_for_user
)
from rest_framework import generics, permissions, filters, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from .serializers import UserListSerializer, UserDetailSerializer, UpdateOwnProfileSerializer
from .permissions import IsOwnerOrAdmin
from .utils import can_view_profile

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        user = serializer.save()
        uid = urlsafe_base64_encode(smart_bytes(user.pk))
        token = email_verification_token.make_token(user)
        verify_url = self.request.build_absolute_uri(reverse('accounts:verify-email'))

        message = f"""
        Hi {user.username},

        Please verify your email by POSTing to:
        {verify_url}

        With JSON:
        {{
            "uid": "{uid}",
            "token": "{token}"
        }}
        """

        send_mail('Verify your SocialConnect email', message, None, [user.email])

class VerifyEmailView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        uidb64 = serializer.validated_data.get('uid')
        token = serializer.validated_data.get('token')

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except Exception:
            return Response({'detail': 'Invalid UID'}, status=status.HTTP_400_BAD_REQUEST)

        if email_verification_token.check_token(user, token):
            user.is_active = True
            user.is_email_verified = True
            user.save()
            return Response({'detail': 'Email verified'})
        return Response({'detail': 'Invalid or expired token'}, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        tokens = get_tokens_for_user(user)
        update_last_login(None, user)
        return Response({
            'access': tokens['access'],
            'refresh': tokens['refresh'],
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            }
        })

class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'detail': 'Refresh token required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'detail': 'Logged out successfully'})
        except Exception:
            return Response({'detail': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)

class PasswordResetView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResetPasswordEmailRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        user = User.objects.filter(email=email).first()

        if user:
            uid = urlsafe_base64_encode(smart_bytes(user.pk))
            token = PasswordResetTokenGenerator().make_token(user)
            reset_url = self.request.build_absolute_uri(reverse('accounts:password-reset-confirm'))
            message = f"""
            Hi {user.username},

            To reset your password, POST to:
            {reset_url}

            With JSON:
            {{
                "uid": "{uid}",
                "token": "{token}",
                "new_password": "your_new_password"
            }}
            """
            send_mail('Password Reset', message, None, [user.email])
        return Response({'detail': 'If the email exists, reset instructions sent'})

class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = SetNewPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        uidb64 = serializer.validated_data['uid']
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except Exception:
            return Response({'detail': 'Invalid UID'}, status=status.HTTP_400_BAD_REQUEST)

        if not PasswordResetTokenGenerator().check_token(user, token):
            return Response({'detail': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        return Response({'detail': 'Password reset successful'})

class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        old_password = serializer.validated_data['old_password']
        new_password = serializer.validated_data['new_password']

        if not request.user.check_password(old_password):
            return Response({'detail': 'Old password incorrect'}, status=status.HTTP_400_BAD_REQUEST)

        request.user.set_password(new_password)
        request.user.save()
        return Response({'detail': 'Password changed successfully'})




class UserListView(generics.ListAPIView):
    """
    GET /api/users/?q=search_term
    Admins see all users. Regular users see public users + followers-only if they follow them.
    """
    serializer_class = UserListSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['username', 'first_name', 'last_name', 'email']

    def get_queryset(self):
        q = self.request.query_params.get('q')
        qs = User.objects.all().select_related('profile')
        # If not admin, filter by visibility
        user = self.request.user if self.request.user.is_authenticated else None
        if not user or not user.is_staff:
            # show public users
            qs = qs.filter(profile__visibility=Profile.VISIBILITY_PUBLIC)
            # optionally support search: if q present broaden
            if q:
                qs = User.objects.filter(username__icontains=q)  # search across usernames, later refine
        return qs.order_by('-date_joined')

class UserDetailView(generics.RetrieveAPIView):
    """
    GET /api/users/<id>/
    Respects profile.visibility
    """
    serializer_class = UserDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'id'
    queryset = User.objects.all().select_related('profile')

    def get(self, request, *args, **kwargs):
        target = self.get_object()
        if not can_view_profile(request.user if request.user.is_authenticated else None, target):
            return Response({'detail': 'Profile is private.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(target)
        return Response(serializer.data)

class MeProfileView(generics.RetrieveUpdateAPIView):
    """
    GET/PUT/PATCH /api/users/me/
    """
    serializer_class = UpdateOwnProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)