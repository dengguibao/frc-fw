from .ipRoute_views import (
    set_route_endpoint,
    set_ip_address_endpoint,
    set_policy_route_endpoint,
    set_interface_state_endpoint,
)
from .iptables_view import (
    get_chain_groups_endpoint,
    set_chain_group_endpoint,
    set_rule_endpoint,
)
from django.urls import path


urlpatterns = [
    path('ipRoute/setRoute', set_route_endpoint),
    path('ipRoute/setIpAddress', set_ip_address_endpoint),
    path('ipRoute/setPolicyRoute', set_policy_route_endpoint),
    path('interface/setIfStatus', set_interface_state_endpoint),

    path('iptables/getChainGroups', get_chain_groups_endpoint),
    path('iptables/setChainGroup', set_chain_group_endpoint),
    path('iptables/setRule/<str:rule_type>', set_rule_endpoint),
]
