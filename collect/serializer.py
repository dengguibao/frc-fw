from .models import *
from rest_framework import serializers


class SysLoadSerialize(serializers.Serializer):
    load1 = serializers.FloatField(required=True, allow_null=False)
    load5 = serializers.FloatField(required=True, allow_null=False)
    load15 = serializers.FloatField(required=True, allow_null=False)
    time = serializers.IntegerField(required=True, allow_null=False)

    def create(self, validated_data):
        return SysLoad.objects.create(**validated_data)

    def update(self, instance, validated_data):
        pass


class MemoryInfoSerialize(serializers.Serializer):
    mem_total = serializers.IntegerField(required=True, allow_null=False)
    mem_free = serializers.IntegerField(required=True, allow_null=False)
    mem_used = serializers.IntegerField(required=True, allow_null=False)
    mem_buff = serializers.IntegerField(required=True, allow_null=False)
    mem_util = serializers.FloatField(required=True, allow_null=False)
    mem_cache = serializers.IntegerField(required=True, allow_null=False)
    time = serializers.IntegerField(required=True, allow_null=False)

    def create(self, validated_data):
        return MemoryInfo.objects.create(**validated_data)

    def update(self, instance, validated_data):
        pass


class CpuInfoSerialize(serializers.Serializer):
    cpu_user = serializers.IntegerField(required=True, allow_null=False)
    cpu_sys = serializers.IntegerField(required=True, allow_null=False)
    cpu_wait = serializers.IntegerField(required=True, allow_null=False)
    cpu_steal = serializers.IntegerField(required=True, allow_null=False)
    cpu_idle = serializers.IntegerField(required=True, allow_null=False)
    cpu_util = serializers.IntegerField(required=True, allow_null=False)
    time = serializers.IntegerField(required=True)

    def create(self, validated_data):
        return CpuInfo.objects.create(**validated_data)

    def update(self, instance, validated_data):
        pass


class IoInfoSerialize(serializers.Serializer):
    block = serializers.CharField(required=True, max_length=10)
    io_rs = serializers.IntegerField(required=True, allow_null=False)
    io_ws = serializers.IntegerField(required=True, allow_null=False)
    io_await = serializers.IntegerField(required=True, allow_null=False)
    io_util = serializers.IntegerField(required=True, allow_null=False)
    time = serializers.IntegerField(required=True, allow_null=False)

    def create(self, validated_data):
        return IoInfo.objects.create(**validated_data)

    def update(self, instance, validated_data):
        pass


class NetInfoSerialize(serializers.Serializer):
    interface = serializers.CharField(required=True, max_length=10, allow_blank=False, allow_null=False)
    in_bytes = serializers.IntegerField(required=True, allow_null=False)
    in_packets = serializers.IntegerField(required=True, allow_null=False)
    in_errors = serializers.IntegerField(required=True, allow_null=False)
    in_drops = serializers.IntegerField(required=True, allow_null=False)
    out_bytes = serializers.IntegerField(required=True, allow_null=False)
    out_packets = serializers.IntegerField(required=True, allow_null=False)
    out_errors = serializers.IntegerField(required=True, allow_null=False)
    out_drops = serializers.IntegerField(required=True, allow_null=False)
    time = serializers.IntegerField(required=True, allow_null=False)

    def create(self, validated_data):
        return NetInfo.objects.create(**validated_data)

    def update(self, instance, validated_data):
        pass


class TcpInfoSerialize(serializers.Serializer):
    tcp_active = serializers.IntegerField(required=True, allow_null=False)
    tcp_passive = serializers.IntegerField(required=True, allow_null=False)
    tcp_inseg = serializers.IntegerField(required=True, allow_null=False)
    tcp_outseg = serializers.IntegerField(required=True, allow_null=False)
    tcp_established = serializers.IntegerField(required=True, allow_null=False)
    tcp_retran = serializers.IntegerField(required=True, allow_null=False)
    time = serializers.IntegerField(required=True, allow_null=False)

    def create(self, validated_data):
        return TcpInfo.objects.create(**validated_data)

    def update(self, instance, validated_data):
        pass
