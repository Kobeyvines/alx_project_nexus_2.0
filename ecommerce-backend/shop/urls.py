from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import CategoryViewSet, ProductViewSet, RegisterView, LogoutView, UserProfileView, AdminUserViewSet

router = DefaultRouter()
router.register(r"categories", CategoryViewSet)
router.register(r"products", ProductViewSet)
router.register(r'users', AdminUserViewSet, basename='users')


urlpatterns = [
    path("",include(router.urls)),
    path("auth/register/", RegisterView.as_view(), name="auth_register"),
    path("auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/logout/", LogoutView.as_view(), name="auth_logout"),
    path("users/me/", UserProfileView.as_view(), name="user-profile"),
]