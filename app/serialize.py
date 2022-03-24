from rest_framework.serializers import ModelSerializer
from .models import OpenVpnUsers


class OpenVpnUsersSerializer(ModelSerializer):
    class Meta:
        model = OpenVpnUsers
        fields = [
            'id', 'username', 'name', 'join_date', 'state', 'user_ip', 'user_route'
        ]
