from django.db import models


class IpAddress(models.Model):
    ip = models.GenericIPAddressField(verbose_name="ip address", null=False, blank=False)
    netmask = models.GenericIPAddressField(verbose_name="netmask", null=False, blank=False)
    ifname = models.CharField(verbose_name="interface name", unique=True, null=False, blank=False, max_length=50)

    def __str__(self):
        return f'ip addr add {self.ip}/{self.netmask} dev {self.ifname}'

    class Meta:
        db_table = 'config_iproute_ipaddr'


class Route(models.Model):
    dst = models.CharField(verbose_name="destination net", null=False, blank=False, max_length=18)
    gateway = models.GenericIPAddressField(verbose_name="gateway", null=False, blank=False)
    ifname = models.CharField(verbose_name="interface name", null=False, blank=False, max_length=50)
    table = models.IntegerField(verbose_name="talbe id", null=True, blank=True)

    def __str__(self):
        table_str = dst_str = ''
        if self.table:
            table_str = f" table {self.table}"
        # if self.netmask:
        #     dst_str = f'{self.dst}/{ip2MaskPrefix(self.netmask)}'
        else:
            dst_str = f'{self.dst}'
        return f'ip route add {dst_str} via {self.gateway} dev {self.ifname}{table_str}'

    class Meta:
        db_table = 'config_iproute_route'
        unique_together = ('dst', 'table')


class SysSetting(models.Model):
    item = models.CharField(verbose_name='config item', max_length=20, unique=True)
    desc = models.CharField(verbose_name='setting description', max_length=50, null=True)
    value = models.BooleanField(default=False)

    def __str__(self):
        return self.item

    @property
    def json(self):
        return {
            'item': self.item,
            'desc': self.desc,
            'value': self.value
        }

    class Meta:
        db_table = 'config_sys_setting'


class PolicyRoute(models.Model):
    src = models.CharField(verbose_name="source address", max_length=18, null=True, blank=True)
    dst = models.CharField(verbose_name="destination addrss", max_length=18, null=True, blank=True)
    sport = models.IntegerField(verbose_name="source port", null=True, blank=True)
    dport = models.IntegerField(verbose_name="destination port", null=True, blank=True)
    mark = models.IntegerField(verbose_name="mark", null=False, blank=False, default=0)
    protocol = models.CharField(verbose_name="protocol", null=True, blank=True, max_length=10)
    # ifname = models.CharField(verbose_name="interface name", null=False, blank=False, max_length=50)
    iif = models.CharField(verbose_name="incoming interface name", null=False, blank=False, max_length=50, default='lo')
    oif = models.CharField(verbose_name="out interface name", null=False, blank=False, max_length=50, default='lo')
    # gateway = models.GenericIPAddressField(verbose_name='gateway')
    table = models.IntegerField(verbose_name="talbe id", null=False, blank=False)

    @property
    def iptables_cmd(self):
        data = [
            'iptables -t mangle -A PREROUTING'
        ]
        if self.iif:
            data.append(f'-i {self.iif}')

        if self.protocol:
            data.append(f'-p {self.protocol}')

        if self.src:
            data.append(f'--src {self.src}')

        if self.sport:
            data.append(f'--sport {self.src}')

        if self.dst:
            data.append(f'--dst {self.dst}')

        if self.dport:
            data.append(f'--dport {self.dport}')

        if self.mark:
            data.append(f'-j MARK --set-mark {self.mark}')

        return ' '.join(data)

    @property
    def iprule_cmd(self):
        data = [
            'ip rule add'
        ]
        if self.src:
            data.append(f"from {self.src}")

        if self.dst:
            data.append(f'to {self.dst}')

        if self.mark:
            data.append(f'fwmark {self.mark}')

        if self.iif:
            data.append(f'iif {self.iif}')

        if self.table:
            data.append(f'table {self.table}')

        return ' '.join(data)

    class Meta:
        db_table = 'config_iproute_policyroute'


class ChainGroup(models.Model):
    TABLE_CHOICE = (
        ('nat', 'nat'),
        ('filter', 'filter')
    )

    GROUP_TYPE_CHOICE = (
        ('snat', 'POSTROUTING'),
        ('dnat', 'PREROUTING'),
        ('filter', 'FORWARD')
    )
    table_name = models.CharField(verbose_name='iptable table name', max_length=10, choices=TABLE_CHOICE, null=False,
                                  blank=False)
    chain_name = models.CharField(verbose_name="custom chain name", unique=True, max_length=50, null=False, blank=False)
    in_interface = models.CharField(verbose_name="in interface", max_length=50, null=True, blank=True)
    src = models.CharField(verbose_name="source addr", max_length=18, null=False, blank=False, default='0.0.0.0/0')
    dst = models.CharField(verbose_name="dst addr", max_length=18, null=False, blank=False, default='0.0.0.0/0')
    group_type = models.CharField(verbose_name='root chain', max_length=10, choices=GROUP_TYPE_CHOICE,
                                  null=False, blank=False)
    pub_date = models.DateTimeField(auto_now_add=True)
    # state = models.BooleanField(default=True, null=False)
    # default = models.CharField(default='ACCEPT', null=False)
    rule_count = models.IntegerField(null=False, blank=False, default=0)

    # root_chain = models.CharField(verbose_name="root chain", null=False, blank=False, choices=GROUP_TYPE_CHOICE)

    @property
    def iptables_cmd(self) -> tuple:
        root_chain = self.get_group_type_display()
        data = [f'iptables -t {self.table_name} -A {root_chain}']

        if self.in_interface and self.group_type == 'filter':
            data.append(f'-i {self.in_interface}')

        if self.src:
            data.append(
                f'-s {self.src}'
            )

        if self.dst:
            data.append(
                f'-d {self.dst}'
            )

        data.append(
            f'-g {self.chain_name}'
        )

        return f'iptables -t {self.table_name} -N {self.chain_name}', ' '.join(data)

    def incrase_rule(self):
        self.rule_count += 1
        self.save()

    def decrase_rule(self):
        if self.rule_count == 0:
            return

        self.rule_count -= 1
        self.save()
        n = 1
        for i in Rule.objects.filter(enable=1, chain=self).order_by('id'):
            i.rule_seq = n
            i.save()
            n += 1

    class Meta:
        db_table = 'config_iptables_chaingroup'
        unique_together = ('chain_name', 'group_type')


class Rule(models.Model):
    chain = models.ForeignKey(ChainGroup, to_field='chain_name', on_delete=models.CASCADE, related_name='rule_chain')
    target = models.CharField(verbose_name='target', null=False, blank=False, max_length=20)
    protocol = models.CharField(verbose_name='protocol', null=True, blank=True, max_length=10)
    to_ports = models.CharField(verbose_name='redirection to-port', null=True, blank=True, max_length=100)
    src = models.CharField(verbose_name='source address', null=True, blank=True, max_length=20, default='0.0.0.0/0')
    dst = models.CharField(verbose_name='destination address', null=True, blank=True, max_length=20,
                           default='0.0.0.0/0')
    sport = models.CharField(verbose_name='source port', null=True, blank=True, max_length=10)
    dport = models.CharField(verbose_name='destination port', null=True, blank=True, max_length=10)
    in_interface = models.CharField(verbose_name='in interface', null=True, blank=True, max_length=20)
    out_interface = models.CharField(verbose_name='out interface', null=True, blank=True, max_length=50)
    to_source = models.CharField(verbose_name='snat to-source', null=True, blank=True, max_length=20)
    to_destination = models.CharField(verbose_name='dnat to-destination', null=True, blank=True, max_length=20)
    comment = models.CharField(verbose_name='comment', null=True, blank=True, max_length=50)
    enable = models.IntegerField(verbose_name='enable', null=False, blank=False, default=1)
    rule_seq = models.IntegerField(verbose_name='rule sequence', null=False, default=-1)
    pub_date = models.DateTimeField(auto_now_add=True)

    # def __str__(self):
    #     return f'{self.src}'

    def update_status(self, state):
        if state:
            self.enable = 1
        else:
            self.enable = 0
        self.save()

    @property
    def json(self):
        origin = {
            'chain_id': self.chain_id,
            'src': self.src,
            'sport': self.sport,
            'dst': self.dst,
            'dport': self.dport,
            'target': self.target,
            'protocol': self.protocol,
            'in_interface': self.in_interface,
            'out_interface': self.out_interface,
            'to_source': self.to_source,
            'to_ports': self.to_ports,
            'to_destination': self.to_destination,
            'comment': self.comment,
            'enable': self.enable
        }

        buff = dict()

        for i in origin:
            if not origin[i]:
                continue
            else:
                buff[i] = origin[i]
        return buff

    def __repr__(self):
        # target_s = protocol_s = to_port_s = src_s = dst_s = sport_s = \
        #     dport_s = in_interface_s = to_source_s = to_destination_s = comment_s = ''
        data = [
            f'iptables -t {self.chain.table_name} -I {self.chain.chain_name}'
        ]

        if self.protocol:
            data.append(f'-p {self.protocol}')

        if self.src:
            data.append(f'--src {self.src}')

        if self.dst:
            data.append(f'--dst {self.dst}')

        if self.sport:
            if ',' in self.sport:
                data.append(f'-m multiport --sports {self.sport.replace(" ","")}')
            else:
                data.append(f'--sport {self.sport}')

        if self.dport:
            if ',' in self.dport:
                data.append(f'-m multiport --dports {self.dport.replace(" ","")}')
            else:
                data.append(f'--dport {self.dport}')

        if self.in_interface:
            data.append(f'-i {self.in_interface}')

        if self.out_interface:
            data.append(f'-o {self.out_interface}')

        if self.target:
            data.append(f'-j {self.target}')

        if self.to_source:
            data.append(f'--to-s ource {self.to_source}')

        if self.to_ports:
            data.append(f'--to-ports {self.to_ports}')

        if self.to_destination:
            data.append(f'--to-destination {self.to_destination}')

        if self.comment:
            data.append(f'-m comment --comment "{self.comment}"')

        return ' '.join(data) if self.enable == 1 else ''

    class Meta:
        db_table = 'config_iptables_rule'


class Vip(models.Model):
    state = (
        ('e', 'enable'),
        ('d', 'disable')
    )
    name = models.CharField(max_length=20, null=False)
    ip_range = models.CharField(max_length=31, null=False)
    isp = models.CharField(max_length=30, null=False)
    state = models.CharField(max_length=1, null=False, choices=state)
    pub_date = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'config_iproute_vip'
        unique_together = (
            'ip_range', 'isp'
        )


def LOAD_DEFAULT_CONFIG():
    from configparser import ConfigParser
    cp = ConfigParser()
    cp.read('global_sys_config_setting.cnf')
    sections = cp.sections()
    config_item = []
    for i in sections:
        if cp.has_option(i, 'desc') and cp.has_option(i, 'value'):
            config_item.append(
                {
                    'item': i,
                    'desc': cp.get(i, 'desc'),
                    'value': cp.get(i, 'value'),
                }
            )
    for i in config_item:
        try:
            res = SysSetting.objects.get(item=i['item'])
            if res.desc != i['desc']:
                res.desc = i['desc']
                res.save()

        except SysSetting.DoesNotExist:
            SysSetting.objects.update_or_create(**i)


LOAD_DEFAULT_CONFIG()
