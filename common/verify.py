from rest_framework.exceptions import ParseError
from django.core.cache import cache
import ipaddress
from pyroute2 import IPDB
import json
import re


def verify_max_value(value: int, max_value: int) -> bool:
    return True if value < max_value else False


def verify_valid_tos(value: str) -> bool:
    return True if value in ('0x00', '0x02', '0x04', '0x08', '0x10') else False


def verify_valid_tcp_port(value: int) -> bool:
    return True if 0 < value <= 65535 else False


def verify_max_length(s: str, max_len: int, no_special=False) -> bool:
    """
    验证最大允许长度
    """
    if no_special:
        if set('[~!@#$%^&*()+{}":;\']+$`') & set(s):
            return False
    return True if len(s) < max_len else False


def verify_interface_name(if_name: str) -> bool:
    """
    verify the if_name whether is invalid interface name
    """
    ipdb = IPDB()
    if_name_list = ipdb.by_name.keys()
    ipdb.release()
    return True if if_name in if_name_list else False


def verify_ip_range(ip_range: str) -> bool:
    """
    verify ip range format
    e.g.
    a.b.c.d-a.b.c.e
    """
    if '-' not in ip_range:
        return False

    ip = ip_range.split('-')
    if len(ip) != 2:
        return False

    ip1 = ip[0]
    ip2 = ip[1]
    if not verify_ip(ip1) or not verify_ip(ip2):
        return False

    if ipaddress.ip_address(ip1) > ipaddress.ip_address(ip2):
        return True
    return False


def verify_interface_state(state: str) -> bool:
    """
    verify interface state whether is up or down
    """
    return True if state.lower() in ('up', 'down') else False


def verify_ip(ip: str) -> bool:
    """
    verify ip address whether is a.b.c.d or a.b.c.d/x
    """
    ip_add = ip_net = False
    try:
        ip_add = ipaddress.ip_address(ip)
    except ValueError:
        pass

    try:
        ip_net = ipaddress.ip_network(ip)
    except ValueError:
        pass

    if ip_add or ip_net:
        return True
    return False


def verify_port_list(value: str) -> bool:
    if ':' in value:
        x = value.split(':')
        if len(x) != 2 or not x[0] or not x[1]:
            return False
        p1 = verify_port(x[0])
        p2 = verify_port(x[1])
        if p1 and p2 and p2 > p1:
            return True
        return False

    if ',' in value:
        for i in value.split(','):
            if verify_port(i):
                continue
            else:
                return False
        return True

    else:
        return verify_port(value)


def verify_port_range(value: str) -> bool:
    if '-' in value and len(value.split('-')) == 2:
        x = value.split('-')
        try:
            p1 = int(x[0])
            p2 = int(x[1])
        except ValueError:
            return False

        if 0 < p1 < 65536 and 0 < p2 < 65536 and p2 > p1:
            return True
        else:
            return False
    else:
        return verify_port(value)


def verify_ip_or_ip_port(value: str) -> bool:
    if ':' in value and len(value.split(':')) == 2:
        try:
            v = value.split(':')
            ipaddress.ip_address(v[0])
            p = int(v[1])
        except ValueError:
            return False

        if v and 0 < p < 65536:
            return True

        return False
    else:
        return verify_ip_addr(value)


def verify_ip_addr(ip: str) -> bool:
    """
    verify ip whether is a invalid ip
    :param ip:
    :return:
    """
    try:
        ipaddress.ip_address(ip)
    except ValueError:
        return False
    return True


def verify_iptables_destination(value: str) -> bool:
    if '-' in value:
        x = value.split(':')
        if len(x) != 2 or not x[0] or not x[1]:
            return False
        ip = verify_ip_addr(x[0])
        port_range = verify_port_range(x[1])
        if ip and port_range:
            return True
        else:
            return False

    else:
        return verify_ip_or_ip_port(value)


def verify_length(data: str, length: int) -> bool:
    """
    验证长度
    """
    return True if len(data) == length else False


def verify_img_verification_code(value: str) -> bool:
    """
    验证图形验证码是否正确
    """
    if not verify_length(value, 5):
        return False

    cached_verification_code = cache.get('img_verify_code_%s' % value.upper())
    if not cached_verification_code:
        return False
    cache.delete('img_verify_code_%s' % value.upper())
    return True


def verify_netmask(ip: str) -> bool:
    """
    verify ip whether is invalid netmask
    :param ip: ip address
    :return:
    """
    result = verify_ip(ip)
    if result:
        valid_dns_num = (128, 192, 224, 240, 248, 252, 254, 255)
        field_num = [int(i) for i in ip.split('.')]
        x = 1
        for i in field_num:
            if i > 0 and i not in valid_dns_num:
                return False
            if x < 4 and field_num[x] > i:
                return False
            x += 1
        return True
    else:
        return False


def verify_ip_subnet(net: str) -> bool:
    """
    verify a.b.c.d/x format subnet
    """
    if '/' not in net or len(net.split('/')) != 2:
        return False
    ip_add = net.split('/')
    if not verify_ip(ip_add[0]):
        return False

    try:
        n = int(ip_add[1])
    except ValueError:
        return False
    except IndexError:
        return False

    if 0 < n > 32:
        return False

    return True
    # try:
    #     ipaddress.ip_network(net)
    # except ValueError:
    #     return False
    # return True


def verify_prefix(prefix: int):
    """
    verify prefix whether is invalid prefix
    """
    return True if 0 <= prefix <= 32 else False


def verify_protocol(protocol: str) -> bool:
    """
    verify iptables rule protocol
    """
    if protocol in ('tcp', 'udp', 'icmp', 'gre', 'ah', 'esp', 'ospf', 'sctp'):
        return True
    return False


def verify_port(p):
    """
    verify port whether is invalid
    """
    try:
        d = int(p)
    except ValueError:
        d = -1

    if 0 < d < 65535:
        return str(p)
    return False


def verify_username(username: str) -> bool:
    """
    verify username whether contain special charset
    """
    # special_char = ('/', ' ', '[', ']', '"', '\\', '\'', '$', '%', '^', '*', '(', ')', '!', '~', '`', '-')
    # for i in special_char:
    #     if i in username:
    #         return False
    # return True
    if len(username) < 0 or len(username) > 20:
        return False

    return False if set('[~!@#$%^&*()+{}":;\']+$`') & set(username) else True


def verify_in_array(arg1: str, array: tuple) -> bool:
    """
    verify arg1 whether in array
    """
    return True if arg1 in array else False


def verify_is_equal(x, y):
    """
    verify two object whether equal
    """
    return True if x == y else False


def verify_field(data: dict, field: tuple):
    """
    verify received dict data
    field format is ('field_name', field_type, verify_func)
    when verify_func is function then call the function verify field content
    when verify_func is tuple then tuple first element is verify_func, the second element is arg
    when field_name start with '*' mean the filed is necessary
    """
    if not isinstance(data, dict):
        return

    buff = dict()
    if isinstance(field, (tuple,list)):
        for field_name, field_type, verify_param in field:
            if field_name[0] == '*':
                field_name = field_name[1:]

                if field_name not in data or (
                        isinstance(data[field_name], bool) and data[field_name] not in (True, False)
                ) or (
                        isinstance(data[field_name], str) and len(data[field_name].strip()) == 0
                ):
                    return 'field %s is necessary and value can not be empty' % field_name

            if field_name not in data:
                continue

            if not isinstance(data[field_name], field_type):
                return 'field %s type wrong!' % field_name

            verify_result = False
            if not verify_param:
                return 'field %s validation tuple is empty'

            if isinstance(verify_param, tuple) and len(verify_param) >= 2:
                if not hasattr(verify_param[0], '__call__'):
                    return 'field %s , first arg is not a function in validation tuple' % field_name

                verify_func = verify_param[0]
                verify_kwargs = None
                verify_arg = verify_param[1]

                if len(verify_param) == 3:
                    verify_kwargs = verify_param[2]

                if verify_kwargs:
                    verify_result = verify_func(data[field_name], verify_arg, verify_kwargs)
                else:
                    verify_result = verify_func(data[field_name], verify_arg)

            if hasattr(verify_param, '__call__'):
                verify_result = verify_param(data[field_name])

            if not verify_result:
                return 'field %s : verify failed!' % field_name

    for i, _, _ in field:
        k = i.strip()
        if k[0] == '*':
            k = k[1:]

        if k in data:

            if isinstance(data[k], (bool, int)):
                buff[k] = data[k]

            if isinstance(data[k], str):
                if len(data[k]) <= 1024:
                    buff[k] = data[k].strip()[0:1024]

                if len(data[k]) == 0:
                    continue

            # buff[k] = data[k].strip() if isinstance(data[k], str) else data[k]
    if not buff:
        return 'return data is empty'

    return buff


def verify_mail(mail: str) -> bool:
    """
    verify mail whether invalid
    """
    return True if re.match("^.+@(\\[?)[a-zA-Z0-9\\-.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(]?)$", mail) else False


def verify_true_false(i) -> bool:
    """
    verify object(i) is true or false
    """
    return True if i in ('1', 1, True, False, 0, '0', 'True', 'False', 'true', 'false') else False


def verify_ip_or_ip_range(value: str) -> bool:
    if '-' in value and verify_ip_range(value):
        return True

    if verify_ip_addr(value):
        return True

    return False


def filter_user_data(data: any, fields: tuple):
    j = dict()
    if isinstance(data, dict):
        j = data
    else:
        if isinstance(data, (bytes, str)):
            try:
                j = json.loads(data)
            except json.decoder.JSONDecodeError:
                raise ParseError('request body is not a json')

    clear_data = verify_field(j, fields)

    if isinstance(clear_data, dict):
        return clear_data
    raise ParseError(clear_data)
