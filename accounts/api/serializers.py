from django.contrib.auth.models import User
from rest_framework import routers, serializers, viewsets
from accounts.models import CustomUser

class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['url', 'username', 'email', 'is_staff', 'is_active', 'date_joined']

