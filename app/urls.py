from django.urls import path
from .openvpn_views import (
    get_openvpn_status,
    start_or_stop_openvpn_server,
    openvpn_op_endpoint,
    get_client_ovpn_file,
    generate_cert,
)

urlpatterns = [
    path('openvpn/getOpenVpnStatus', get_openvpn_status),
    path('openvpn/startOrStopServer', start_or_stop_openvpn_server),
    path('openvpn/openVpnUserSet', openvpn_op_endpoint),
    path('openvpn/genCert', generate_cert),
    path('openvpn/ovpnDownload/<int:uid>/', get_client_ovpn_file)
]