from .models import *
from config.models import PolicyRoute
from rest_framework import serializers
import time


class IptablesEventSerialize(serializers.ModelSerializer):
    class Meta:
        model = IptablesEvent
        fields = '__all__'


class PolicyRouteSerialize(serializers.ModelSerializer):
    class Meta:
        model = PolicyRoute
        fields = '__all__'


class SysLoadSerialize(serializers.ModelSerializer):
    datetime = serializers.SerializerMethodField()

    def get_datetime(self, obj):
        return time.strftime('%H:%M:%S', time.localtime(obj.time))

    class Meta:
        model = SysLoad
        fields = '__all__'


class MemoryInfoSerialize(SysLoadSerialize):
    class Meta:
        model = MemoryInfo
        fields = '__all__'


class CpuInfoSerialize(SysLoadSerialize):
    class Meta:
        model = CpuInfo
        fields = '__all__'


class IoInfoSerialize(SysLoadSerialize):
    class Meta:
        model = IoInfo
        fields = '__all__'


class NetInfoSerialize(SysLoadSerialize):
    class Meta:
        model = NetInfo
        fields = '__all__'


class TcpInfoSerialize(SysLoadSerialize):
    class Meta:
        model = TcpInfo
        fields = '__all__'
