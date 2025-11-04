from users.session_manager import create_session, get_session
from users.session_manager import delete_session
from rest_framework.permissions import AllowAny
import uuid
from rest_framework import generics
from users.serializers import UserCreateSerializer, UserSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from users.serializers import CustomTokenObtainPairSerializer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework_simplejwt.views import TokenObtainPairView
from users.serializers import CustomTokenObtainPairSerializer
from users.session_manager import create_session
from rest_framework.response import Response
import uuid

class RegisterFanView(generics.CreateAPIView):
    serializer_class = UserCreateSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        serializer.save(role='fan')


class RegisterPromoterView(generics.CreateAPIView):
    serializer_class = UserCreateSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        serializer.save(role='promoter')


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_data = serializer.validated_data['user']
        refresh_token_str = serializer.validated_data['refresh']
        access = serializer.validated_data['access']

        refresh = RefreshToken(refresh_token_str)
        jti = refresh.get("jti")

        csrf_token = str(uuid.uuid4())
        session_id = create_session(user_data['id'], csrf_token, jti=jti)

        client_type = request.headers.get('X-Client-Type', '').lower()

        if client_type == 'mobile':
            response = Response({
                'refresh': str(refresh),
                'access': str(access),
                'csrf_token': csrf_token,
                'session_id': session_id,
                'user': user_data,
            })
            return response
        else:
            response = Response({'user': user_data})

            response.set_cookie('access_token', str(access), httponly=True, samesite='Strict', path='/')#, max_age=1900)
            response.set_cookie('refresh_token', str(refresh), httponly=True, samesite='Lax', path='/')#, max_age=7 * 24 * 60 *60)
            response.set_cookie('session_id', session_id, httponly=True, samesite='Strict', path='/')#, max_age=7200)
            response.set_cookie('csrf_token', csrf_token, httponly=False, samesite='Strict', path='/')#, max_age=7200)

            return response


@method_decorator(csrf_exempt, name='dispatch')
class RefreshAccessFromCookieView(APIView):
    permission_classes = []  # Public endpoint (no token needed yet)

    def post(self, request):
        if not request.user or request.user.is_anonymous:
            return Response({"detail": "Authentification requise."}, status=status.HTTP_401_UNAUTHORIZED)
        refresh_token = request.COOKIES.get('refresh_token')
        session_id = request.COOKIES.get('session_id')

        if not refresh_token or not session_id:
            raise AuthenticationFailed('Missing refresh token or session ID.')

        session = get_session(session_id)
        if not session:
            raise AuthenticationFailed('Invalid or expired session.')

        try:
            refresh = RefreshToken(refresh_token)
            user_id = refresh['user_id']
            jti = refresh.get('jti')

            if session.get('user_id') != user_id:
                raise AuthenticationFailed('Session does not match user.')

            if session.get('refresh_jti') != jti:
                raise AuthenticationFailed('Token has been rotated or invalid.')

            refresh.blacklist()
            new_refresh = RefreshToken.for_user(request.user)
            new_access = str(new_refresh.access_token)
            new_jti = new_refresh['jti']
            
            new_csrf_token = str(uuid.uuid4())
            delete_session(session_id)
            new_session_id = create_session(user_id, new_csrf_token, jti=new_jti)

        except TokenError:
            raise AuthenticationFailed('Invalid or expired refresh token.')

        response = Response({'message': 'Access token refreshed'})

        response.set_cookie('access_token', new_access, httponly=True, samesite='Strict', path='/')#, max_age=30 * 60)
        response.set_cookie('refresh_token', str(new_refresh), httponly=True, samesite='Lax', path='/')#, max_age=7 * 24 * 60 * 60)
        response.set_cookie('session_id', new_session_id, httponly=True, samesite='Strict', path='/')#, max_age=7200)
        response.set_cookie('csrf_token', new_csrf_token, httponly=False, samesite='Strict', path='/')#, max_age=7200)

        return response


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response({'user': serializer.data})


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        session_id = request.COOKIES.get('session_id')
        refresh_token = request.COOKIES.get('refresh_token')
        if session_id:
            delete_session(session_id)

        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except Exception:
                pass

        # Clear the cookie
        response = Response({'message': 'Logged out'})
        response.delete_cookie('access_token', path='/', samesite='Strict')
        response.delete_cookie('refresh_token', path='/', samesite='Lax')
        response.delete_cookie('session_id', path='/', samesite='Strict')
        response.delete_cookie('csrf_token', path='/', samesite='Strict')

        return response

