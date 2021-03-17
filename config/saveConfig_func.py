from pyroute2 import IPRoute
from pyroute2 import IPDB


def all_route_table():
    ipdb = IPDB()
    ifname_list = ipdb.by_name.keys()
    ipr = IPRoute()
    x = ipr.route('dump')
    data = []
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

        buf['add'] = f'{dst_addr}/{dst_len}'
        if gw:
            buf['via'] = gw
        if if_idx:
            buf['dev'] = ifname_list[if_idx-1]
        if metric:
            buf['metric'] = '%s' % metric
        buf['table'] = '%s' % table

        cmd = ['ip', 'route']
        for b in buf.items():
            cmd.append(' '.join(b))

        data.append(' '.join(cmd))
        del buf, cmd

    return data


# def all_rule_table():
#     data = []
#     x = IPRoute()
#     for i in x.rule('dump'):
#         # print(i)
#         buf = {}
#
#         dst_len = i['dst_len']
#         src_len = i['src_len']
#         table = i['table']
#         tos = i['tos']
#         dst_addr = i.get_attr('FRA_DST')
#         src_addr = i.get_attr('FRA_SRC') if i.get_attr('FRA_SRC') else '0.0.0.0'
#         priority = i.get_attr('FRA_PRIORITY')
#
#         if src_addr:
#             buf['from'] = f'{src_addr}/{src_len}'
#
#         if dst_addr:
#             buf['to'] = f'{dst_addr}/{dst_len}'
#
#         if tos:
#             buf['tos'] = '%s' % tos
#
#         buf['priority'] = str(priority) if priority else '0'
#         buf['table'] = '%s' % table
#
#         cmd = ['ip', 'rule', 'add']
#         for b in buf.items():
#             cmd.append(' '.join(b))
#
#         data.append(' '.join(cmd))
#         del buf, cmd
#     x.close()
#
#     return data


def all_interface_adrr():
    ip = IPDB()
    x = ip.interfaces
    data = []
    for i in x:

        if isinstance(i, int) or x[i]['operstate'] != 'UP':
            continue
        # print(x[i])
        ifname = x[i]['ifname']
        addr = x[i]['ipaddr'][0]['address']
        prefix = x[i]['ipaddr'][0]['prefixlen']
        ip_addr = '%s/%s' % (addr, prefix)
        buf = ('ip', 'addr', 'add', ip_addr, 'dev', ifname)
        data.append(' '.join(buf))
    ip.release()
    return data
#
# m = (
#     all_interface_adrr,
#     all_route_table,
#     all_rule_table,
# )
#
# for backup_method in m:
#     for item in backup_method():
#         print(item)
#     print('#', '-'*30)
