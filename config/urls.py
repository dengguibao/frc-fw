from .iproute_views import (
    set_route_endpoint,
    set_ip_address_endpoint
)
from django.urls import path


urlpatterns = [
    path('ipRoute/setRoute', set_route_endpoint),
    path('ipRoute/setIpAddress', set_ip_address_endpoint),
]
