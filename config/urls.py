from .ipRoute_views import (
    set_ip_route_endpoint,
    set_ip_address_endpoint,
    set_ip_rule_endpoint,
    # set_interface_state_endpoint,
)
from .iptables_view import set_chain_group_endpoint, set_rule_endpoint, change_rule_seq_endpoint
from .sys_views import sys_setting_endpoint, ip_set_endpoint
from .save_config import get_running_config_endpoint, write_config_endpoint
from .vip_views import set_vip_set_endpoints, get_all_vip_address_endpoint

from django.urls import path


urlpatterns = [
    path('ipRoute/setRoute', set_ip_route_endpoint),
    path('ipRoute/setIpAddress', set_ip_address_endpoint),
    path('ipRoute/setRule', set_ip_rule_endpoint),
    # path('interface/setIfState', set_interface_state_endpoint),


    path('iptables/setChainGroup', set_chain_group_endpoint),
    path('iptables/setRule/<str:rule_type>', set_rule_endpoint),
    path('iptables/changeRule', change_rule_seq_endpoint),
    #
    # path('sys/setFoward', set_forward_state_endpoint),
    path('sys/getRunningConfig', get_running_config_endpoint),
    path('sys/saveRunningConfig', write_config_endpoint),
    path('sys/ipset', ip_set_endpoint),
    # path('sys/recordIptablesEvent', record_iptables_event_endpoint),

    path('sys/sysConfig', sys_setting_endpoint),

    path('vip/setVip', set_vip_set_endpoints),
    path('vip/getVipAddress', get_all_vip_address_endpoint)
]
