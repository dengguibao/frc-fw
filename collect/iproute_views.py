from pyroute2 import IPRoute
from pyroute2 import IPDB

from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.response import Response


from common.functions import prefix2NetMask


@api_view(['GET'])
def get_static_route_table_endpoint(request):
    table = request.GET.get('interface_index', 254)
    try:
        table = int(table)
    except:
        table = 254
    ipdb = IPDB()
    ifname_list = ipdb.by_name.keys()
    ipr = IPRoute()
    x = ipr.route('dump', table=table)
    route_table = []
    for i in x:
        buf = {}
        dst_len = i['dst_len']
        table = i['table']
        dst_addr = i.get_attr('RTA_DST') if i.get_attr('RTA_DST') else '0.0.0.0'
        gw = i.get_attr('RTA_GATEWAY')
        metric = i.get_attr('RTA_PRIORITY')
        if_idx = i.get_attr('RTA_OIF')

        if not if_idx:
            continue

        buf['destination'] = dst_addr
        buf['netmask'] = prefix2NetMask(dst_len)
        if gw:
            buf['gateway'] = gw
        if if_idx:
            buf['iface'] = ifname_list[if_idx - 1]
        if metric:
            buf['metric'] = metric
        buf['table'] = table
        buf['prefix'] = dst_len
        route_table.append(buf)
        del buf
    ipr.close()
    ipdb.release()

    # is_title = True
    # route_table = []
    # with open('/proc/net/route') as fp:
    #     for line in fp:
    #         if is_title:
    #             is_title = False
    #             continue
    #         line_field = line.split()
    #         netmask = hexStr2Ip(line_field[7])
    #         route_table.append({
    #             "iface": line_field[0],
    #             "destination": hexStr2Ip(line_field[1]),
    #             "gateway": hexStr2Ip(line_field[2]),
    #             "netmask": netmask,
    #             "prefix": ip2MaskPrefix(netmask),
    #             "metric": line_field[6]
    #         })
    return Response({
        "code": 0,
        "msg": "success",
        "data": route_table
    }, status=status.HTTP_200_OK)


@api_view(('GET',))
def get_all_ip_rule_endpoint(request):
    data = []
    all_if = IPDB().by_name.keys()
    sys_table_name = {
        253: 'local',
        254: 'main',
        255: 'default',
    }
    with IPRoute() as x:
        for i in x.rule('dump'):
            buf = {}
            dst_len = i['dst_len']
            src_len = i['src_len']
            table = i['table']
            tos = i['tos']
            dst_addr = i.get_attr('FRA_DST') if i.get_attr('FRA_DST') else '0.0.0.0'
            src_addr = i.get_attr('FRA_SRC') if i.get_attr('FRA_SRC') else '0.0.0.0'
            priority = i.get_attr('FRA_PRIORITY')

            buf['from'] = f'{src_addr}/{src_len}'
            buf['to'] = f'{dst_addr}/{dst_len}'
            buf['tos'] = '%s' % tos
            print(table)
            buf['table_name'] =sys_table_name[table] if table in (253, 254, 255) else all_if[table-1]

            buf['priority'] = str(priority) if priority else '0'
            buf['table'] = '%s' % table
            data.append(buf)
            del buf

    return Response({
        'code': 0,
        'msg': 'success',
        'data': data
    })


