""" urls user for view"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from users.views.auth import (
    CurrentUserView,
    LogoutView,
    RefreshAccessFromCookieView,
    RegisterFanView,
    RegisterPromoterView,
    CustomTokenObtainPairView,
)

from users.views.protected import (
    AdminOnlyView,
    PromoterOnlyView,
    ArtistOnlyView,
    FanOnlyView
)


urlpatterns = [
    path('register/fan/', RegisterFanView.as_view()),
    path('register/promoter/', RegisterPromoterView.as_view()),
    path('login/', CustomTokenObtainPairView.as_view()),
    path('token/refresh/', TokenRefreshView.as_view()),
    path('token/refresh-from-cookie/', RefreshAccessFromCookieView.as_view()),
    path('me/', CurrentUserView.as_view()),
    path('logout/', LogoutView.as_view()),

    path('admin-area/', AdminOnlyView.as_view()),
    path('promoter-area/', PromoterOnlyView.as_view()),
    path('artist-area/', ArtistOnlyView.as_view()),
    path('fan-area/', FanOnlyView.as_view()),
]
