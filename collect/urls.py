from .interface_views import get_interface_detail_endpoint, get_interface_list_endpoint
from .basic_views import get_basic_info_endpoint, get_sys_forward_state_endpoint
from .iproute_views import get_static_route_table_endpoint, get_all_ip_rule_endpoint
from .sar_views import sar_info_endpoint, clean_sar_data_endpoint
from .iptables_view import get_chain_groups_endpoint


from django.urls import path


urlpatterns = [
    path('sar/<str:name>', sar_info_endpoint),
    path('basicInfo', get_basic_info_endpoint),
    path('ipRoute/getStaticRouteTable', get_static_route_table_endpoint),
    path('interface/getInterfaceList', get_interface_list_endpoint),
    path('interface/getInterfaceDetail', get_interface_detail_endpoint),
    path('sarClear', clean_sar_data_endpoint),
    path('ipRoute/getAllIpRule', get_all_ip_rule_endpoint),
    path('iptables/getChainGroups', get_chain_groups_endpoint),
    path('sys/getFowardState', get_sys_forward_state_endpoint),
]
