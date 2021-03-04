from .views import (
    sar_info_endpoint,
    get_basic_info_endpoint,
    get_static_route_table_endpoint,
    get_interface_list_endpoint,
    get_interface_detail_endpoint,
    clean_sar_data_endpoint,
)
from django.urls import path


urlpatterns = [
    path('server/sar/<str:name>', sar_info_endpoint),
    path('server/basicInfo', get_basic_info_endpoint),
    path('server/ipRoute/getStaticRouteTable', get_static_route_table_endpoint),
    path('server/ipRoute/getInterfaceList', get_interface_list_endpoint),
    path('server/ipRoute/getInterfaceDetail', get_interface_detail_endpoint),
    path('server/sarClear', clean_sar_data_endpoint),
]
