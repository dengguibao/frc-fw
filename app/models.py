import configparser
import os

import iptc.easy
from django.conf import settings
from django.db import models
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from common.exec_command import send_command
from common.functions import get_file_content, ip2MaskPrefix

OVPN_TEMP = """
client
remote {listen_ip} {listen_port}
dev tun
proto udp
ca ca.crt
cert client.crt
key client.key
tls-auth ta.key 1
remote-cert-tls server
resolv-retry infinite
nobind
persist-key
persist-tun
comp-lzo
verb 3
mute-replay-warnings
<ca>
{ca_str}
</ca>

<cert>
{cert_str}
</cert>

<key>
{key_str}
</key>

key-direction 1

<tls-auth>
{tls_str}
</tls-auth>
"""


class OpenVpnUsers(models.Model):
    name = models.CharField(max_length=8, null=False, verbose_name='nickname')
    username = models.CharField(max_length=20, unique=True, verbose_name='vpn account name', null=False)
    join_date = models.DateTimeField(auto_now_add=True,)
    state = models.BooleanField(default=True)
    user_crt = models.TextField(null=True)
    user_key = models.TextField(null=True)
    user_ip = models.GenericIPAddressField(null=False, default=0)
    user_route = models.TextField(null=False, default='0.0.0.0 0.0.0.0')
    # ovpn_file = models.TextField(null=False)

    def build_ovpn_file(self):
        cp = configparser.ConfigParser()
        cp.read(settings.APP_SETTING_FILE)
        return OVPN_TEMP.format(
            ca_str='\n'.join(get_file_content('/etc/openvpn/ca.crt')),
            listen_ip=cp.get('openvpn', 'listen_ip'),
            listen_port=cp.get('openvpn', 'listen_port'),
            cert_str=self.user_crt,
            key_str=self.user_key,
            tls_str='\n'.join(get_file_content('/etc/openvpn/ta.key'))
        )

    class Meta:
        db_table = 'app_openvpn_users'


@receiver(post_save, sender=OpenVpnUsers)
def handle_create_user(sender, instance, created, **kwargs):
    if created:
        if send_command('bash', './app/openvpn_add_user.sh', instance.username):
            instance.user_crt = '\n'.join(get_file_content('/etc/openvpn/easy-rsa/keys/%s.crt' % instance.username))
            instance.user_key = '\n'.join(get_file_content('/etc/openvpn/easy-rsa/keys/%s.key' % instance.username))
            instance.save()
        else:
            instance.delete()
            return

        try:
            # 写入规则至iptables
            cp = configparser.ConfigParser()
            cp.read(settings.APP_SETTING_FILE)
            subnet = cp.get('openvpn', 'server').split()

            ccd_list = [f'ifconfig-push {instance.user_ip} {subnet[1]}']

            for i in instance.user_route.splitlines():
                if not i.strip():
                    continue
                ccd_list.append(f'push "route {instance.user_route}"')
                route_ip = i.split()
                iptc.easy.insert_rule('filter', '__SYS_OPENVPN_RULE__', {
                    'src': instance.user_ip,
                    'dst': f'{route_ip[0]}/{ip2MaskPrefix(route_ip[1])}',
                    'target': 'ACCEPT',
                    'comment': f'{instance.username} incoming'
                })
                iptc.easy.insert_rule('filter', '__SYS_OPENVPN_RULE__', {
                    'src': f'{route_ip[0]}/{ip2MaskPrefix(route_ip[1])}',
                    'dst': instance.user_ip,
                    'target': 'ACCEPT',
                    'comment': f'{instance.username} back'
                })
            # 写ccd文件
            with open(f'/etc/openvpn/ccd/{instance.username}', 'w+') as fp:
                fp.write(os.linesep.join(ccd_list))
        except:
            instance.delete()


@receiver(pre_delete, sender=OpenVpnUsers)
def handle_delete_user(sender, instance, **kwargs):
    if send_command('bash', './app/openvpn_remove_user.sh', instance.username):
        for i in instance.user_route.splitlines():
            if not i.strip():
                continue

            route_ip = i.split()
            iptc.easy.delete_rule('filter', '__SYS_OPENVPN_RULE__', {
                'src': instance.user_ip,
                'dst': f'{route_ip[0]}/{ip2MaskPrefix(route_ip[1])}',
                'target': 'ACCEPT',
                'comment': f'{instance.username} incoming'
            })
            iptc.easy.delete_rule('filter', '__SYS_OPENVPN_RULE__', {
                'src': f'{route_ip[0]}/{ip2MaskPrefix(route_ip[1])}',
                'dst': instance.user_ip,
                'target': 'ACCEPT',
                'comment': f'{instance.username} back'
            })
            if os.path.exists('/etc/openvpn/ccd/'+instance.username):
                os.remove('/etc/openvpn/ccd/'+instance.username)
        return True
    return False
