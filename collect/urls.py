from .interface_views import get_interface_detail_endpoint, get_interface_list_endpoint
from .basic_views import get_basic_info_endpoint, get_sys_forward_state_endpoint
from .iproute_views import get_static_route_table_endpoint, get_all_ip_rule_endpoint, get_arp_tables_endpoints
from .sar_views import sar_info_endpoint, clean_sar_data_endpoint, clear_iptables_event, get_disk_usage_endpoint
from .iptables_view import (
    get_iptables_chains_endpoint,
    get_iptables_rules_endpoint,
    iptables_chain_aggregation_endpoint,
    iptables_event_endpoint,
)
from .session_views import get_system_conn_sessions, get_session_host_count


from django.urls import path


urlpatterns = [
    path('sar/<str:name>', sar_info_endpoint),
    path('disk_usage', get_disk_usage_endpoint),
    path('arp', get_arp_tables_endpoints),
    path('basicInfo', get_basic_info_endpoint),
    path('ipRoute/getStaticRouteTable', get_static_route_table_endpoint),
    path('interface/getInterfaceList', get_interface_list_endpoint),
    path('interface/getInterfaceDetail', get_interface_detail_endpoint),
    path('sarClear', clean_sar_data_endpoint),
    path('iptablesEventClear', clear_iptables_event),
    path('ipRoute/getAllIpRule', get_all_ip_rule_endpoint),
    path('iptables/getAllChain', get_iptables_chains_endpoint),
    path('iptables/aggregation/chainRule', iptables_chain_aggregation_endpoint),
    path('iptables/event', iptables_event_endpoint),
    path('iptables/getAllRulesByChain', get_iptables_rules_endpoint),
    path('sys/getFowardState', get_sys_forward_state_endpoint),
    path('getSysConnSessions', get_system_conn_sessions),
    path('hostSessionCount', get_session_host_count),
]
