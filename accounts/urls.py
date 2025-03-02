from django.urls import path, include
from rest_framework.routers import DefaultRouter
from accounts.api.views import UserViewSet, LogoutView, LoginView
router = DefaultRouter()
router.register(r'users', UserViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/logout/', LogoutView.as_view(), name='logout'),
    path('api/login/', LoginView.as_view(), name='login'),
]