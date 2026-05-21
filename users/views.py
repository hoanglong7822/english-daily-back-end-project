from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import RegisterSerializer, UserSerializer


class RegisterView(APIView):
    """
    POST /api/auth/register/
    Body: { username, email, password, password2 }
    """

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response(
                {
                    'user': UserSerializer(user).data,
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """
    POST /api/auth/login/
    Body: { username, password }
    """

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response(
                {'detail': 'Username and password are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(
                {'detail': 'Invalid credentials.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.check_password(password):
            return Response(
                {'detail': 'Invalid credentials.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_active:
            return Response(
                {'detail': 'Account is disabled.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        )


class LogoutView(APIView):
    """
    POST /api/auth/logout/
    Header: Authorization: Bearer <access_token>
    Body: { refresh: "<refresh_token>" }
    Blacklists the refresh token so it can't be reused.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response(
                {'detail': 'Refresh token is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            return Response(
                {'detail': 'Invalid or expired token.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({'detail': 'Successfully logged out.'}, status=status.HTTP_200_OK)


class UserListView(APIView):
    """
    GET /api/auth/users/
    Header: Authorization: Bearer <access_token>
    Chỉ admin (is_staff=True) mới được gọi.
    """

    permission_classes = [IsAdminUser]

    def get(self, request):
        users = User.objects.all().order_by('id')
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)


class MeView(APIView):
    """
    GET /api/auth/me/
    Header: Authorization: Bearer <access_token>
    Trả về thông tin của user đang đăng nhập.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class UserDetailView(APIView):
    """
    GET /api/auth/users/<id>/
    Header: Authorization: Bearer <access_token>
    Admin xem bất kỳ user, user thường chỉ xem chính mình.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        # Non-admin users can only view their own profile
        if not request.user.is_staff and request.user.pk != pk:
            return Response(
                {'detail': 'You do not have permission to view this user.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response(
                {'detail': 'User not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = UserSerializer(user)
        return Response(serializer.data)
