import os.path

from rest_framework.response import Response

from common.exec_command import send_command
from rest_framework.decorators import api_view
from rest_framework.exceptions import ParseError


@api_view(('GET',))
def get_session_host_count(request):

    ret = send_command(
        'conntrack', '-L',
        out=True
    )
    hits = dict()
    if ret:
        for line in ret.splitlines():
            if 'src=127.0.0.1' in line:
                continue
            for i in line.split():
                if 'src=' in i:
                    x = i.split('=')
                    if x[1] in hits:
                        hits[x[1]] += 1
                    else:
                        hits[x[1]] = 1
                    break
        return Response({
            'msg': 'success',
            'data': [{'host': k, 'hits': v} for k, v in hits.items()]
        })
    raise ParseError('server internal error')


@api_view(('GET',))
def get_system_conn_sessions(request):
    if not os.path.exists('/usr/sbin/conntrack'):
        raise ParseError('system not install conntrack')
    send_command('conntrack', '-D', '-s', '127.0.0.1')
    result = send_command('conntrack', '-L', out=True)
    # print(result)
    if result:
        return Response({
            'msg': 'success',
            'data': build_session_data(result.splitlines())
        })
    raise ParseError('command execute not success')


def build_session_data(origin_session: list) -> list:
    data = []

    for i in origin_session:
        if 'conntrack' in i:
            print('continue')
            continue

        flag = None
        protocol = None
        mark = None
        recv_src = None
        tx_src = None
        recv_dst = None
        tx_dst = None
        recv_sport = None
        tx_sport = None
        recv_dport = None
        tx_dport = None
        ttl = None

        field = i.split()
        # CLOSE
        # CLOSE_WAIT
        # ESTABLISHED
        # FIN_WAIT
        # LAST_ACK
        # NONE
        # SYN_RECV
        # SYN_SENT
        # SYN_SENT2
        # TIME_WAIT
        for x in field:
            if x in (
                    'TIME_WAIT', 'ESTABLISHED', 'SYN_SENT',
                    'SYN_RECV', 'CLOSE', 'CLOSE_WAIT', 'FIN_WAIT',
                    'LAST_ACK', 'NONE', 'SYN_SENT2'):
                flag = x
            protocol = field[0]
            ttl = field[2]
            if 'src=' in x:
                if not recv_src:
                    recv_src = x.split('=')[1]
                tx_src = x.split('=')[1]

            if 'dst=' in x:
                if not recv_dst:
                    recv_dst = x.split('=')[1]
                tx_dst = x.split('=')[1]

            if 'sport=' in x:
                if not recv_sport:
                    recv_sport = x.split('=')[1]
                tx_sport = x.split('=')[1]

            if 'dport=' in x:
                if not recv_dport:
                    recv_dport = x.split('=')[1]
                tx_dport = x.split('=')[1]

            if 'mark=' in x:
                mark = x.split('=')[1]

        data.append(
            {
                'tcp_flag': flag,
                'protocol': protocol.upper(),
                'ttl': ttl,
                'req_src': f'{recv_src}' + (f':{recv_sport}' if recv_sport else ''),
                'req_dst': f'{recv_dst}' + (f':{recv_dport}' if recv_dport else ''),

                'rep_src': f'{tx_src}' + (f':{tx_sport}' if tx_sport else ''),
                'rep_dst': f'{tx_dst}' + (f':{tx_dport}' if tx_dport else ''),
                'mark': mark
            }
        )
    return data
