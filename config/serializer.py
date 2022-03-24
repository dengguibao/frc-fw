from rest_framework.serializers import ModelSerializer
from .models import Rule, ChainGroup, Vip


class VipSerialize(ModelSerializer):
    class Meta:
        model = Vip
        fields = '__all__'


class Chain(ModelSerializer):
    class Meta:
        model = ChainGroup
        fields = '__all__'


class Rules(ModelSerializer):
    chain = Chain()

    class Meta:
        model = Rule
        fields = '__all__'
