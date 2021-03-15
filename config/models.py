from django.db import models
from common.functions import ip2MaskPrefix


class IpAddress(models.Model):
    ip = models.IPAddressField(verbose_name="ip address", null=False, blank=False)
    netmask = models.IPAddressField(verbose_name="netmask", null=False, blank=False)
    ifname = models.CharField(verbose_name="interface name", unique=True, null=False, blank=False, max_length=50)

    def __str__(self):
        return f'ip addr add {self.ip}/{self.netmask} dev {self.ifname}'

    class Meta:
        db_table = 'config_iproute_ipaddr'


class Route(models.Model):
    dst = models.CharField(verbose_name="destination net", null=False, blank=False, max_length=18)
    gateway = models.IPAddressField(verbose_name="gateway", null=False, blank=False)
    ifname = models.CharField(verbose_name="interface name", null=False, blank=False, max_length=50)
    table = models.IntegerField(verbose_name="talbe id", null=True, blank=True)

    def __str__(self):
        table_str = dst_str = ''
        if self.table:
            table_str = f" table {self.table}"
        if self.netmask:
            dst_str = f'{self.dst}/{ip2MaskPrefix(self.netmask)}'
        else:
            dst_str = f'{self.dst}'
        return f'ip route add {dst_str} via {self.gateway} dev {self.ifname}{table_str}'

    class Meta:
        db_table = 'config_iproute_route'
        unique_together = ('dst', 'table')


class PolicyRoute(models.Model):
    src = models.IPAddressField(verbose_name="source address", null=True, blank=True)
    dst = models.IPAddressField(verbose_name="destination addrss", null=True, blank=True)
    src_len = models.IntegerField(verbose_name="source address prefix", null=True, blank=True)
    dst_len = models.IntegerField(verbose_name="destination address prefix", null=True, blank=True)
    priority = models.IntegerField(verbose_name="priority", null=True, blank=True)
    tos = models.CharField(verbose_name="type of service", null=True, blank=True, max_length=50)
    ifname = models.CharField(verbose_name="interface name", null=False, blank=False, max_length=50)
    table = models.IntegerField(verbose_name="talbe id", null=True, blank=True)

    def __str__(self):
        pri_str = src_str = dst_str = tos_str = table_str = ''
        if self.src:
            src_str = f" from {self.src}"

        if self.dst:
            dst_str = f' to {self.dst}'

        if self.src and self.src_len:
            src_str = f' from {self.src}/{self.src_len}'

        if self.dst and self.dst_len:
            dst_str = f' from {self.dst}/{self.dst_len}'

        if self.priority:
            pri_str = f' priority {self.priority}'

        if self.tos:
            tos_str = f' tos {self.tos}'

        if self.table:
            table_str = f' stable {self.table}'

        return f'ip rule add {src_str}{dst_str}{tos_str}{pri_str}{table_str}'

    class Meta:
        db_table = 'config_iproute_policyroute'
        unique_together = ('src', 'dst', 'src_len', 'dst_len', 'tos', 'table')


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
    group_type = models.CharField(verbose_name='iptable table name', max_length=10, choices=GROUP_TYPE_CHOICE,
                                  null=False, blank=False)
    pub_date = models.DateTimeField(auto_now_add=True)

    # root_chain = models.CharField(verbose_name="root chain", null=False, blank=False, choices=GROUP_TYPE_CHOICE)

    def __str__(self):
        root_chain = self.get_group_type_display()
        return f'iptables -t {self.table_name} -N {self.chain_name}\niptables -t {self.table_name} -I {root_chain} -j {self.chain_name}'

    class Meta:
        db_table = 'config_iptables_chaingroup'
        unique_together = ('chain_name', 'group_type')


class Rule(models.Model):
    chain = models.ForeignKey(ChainGroup, to_field='chain_name')
    target = models.CharField(verbose_name='target', null=False, blank=False, max_length=20)
    protocol = models.CharField(verbose_name='protocol', null=True, blank=True, max_length=10)
    to_port = models.CharField(verbose_name='redirection to-port', null=True, blank=True, max_length=10)
    src = models.CharField(verbose_name='source address', null=True, blank=True, max_length=20)
    dst = models.CharField(verbose_name='destination address', null=True, blank=True, max_length=20)
    sport = models.CharField(verbose_name='source port', null=True, blank=True, max_length=10)
    dport = models.CharField(verbose_name='destination port', null=True, blank=True, max_length=10)
    in_interface = models.CharField(verbose_name='in interface', null=True, blank=True, max_length=20)
    to_source = models.CharField(verbose_name='snat to-source', null=True, blank=True, max_length=20)
    to_destination = models.CharField(verbose_name='dnat to-destination', null=True, blank=True, max_length=20)
    comment = models.CharField(verbose_name='comment', null=True, blank=True, max_length=50)
    enable = models.IntegerField(verbose_name='enable', null=False, blank=False)
    pub_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        target_s = protocol_s = to_port_s = src_s = dst_s = sport_s = dport_s = in_interface_s = to_source_s = to_destination_s = comment_s = ''
        if self.target:
            target_s = f' -j {self.target}'

        if self.protocol:
            protocol_s = f' -p {self.protocol}'

        if self.to_port:
            to_port_s = f' --to-port {self.to_port}'

        if self.src:
            src_s = f' --src {self.src}'

        if self.dst:
            dst_s = f' --dst {self.dst}'

        if self.sport:
            sport_s = f' --sport {self.sport}'

        if self.dport:
            dport_s = f' --dport {self.dport}'

        if self.in_interface:
            in_interface_s = f' -i {self.in_interface}'

        if self.to_source:
            to_source_s = f' --to-source {self.to_source}'

        if self.to_destination:
            to_destination_s = f' --to-destination {self.to_destination}'

        if self.comment:
            comment_s = f' -m comment --comment "{self.comment}"'

        return f'iptables -t {self.chain.table_name} -I {self.chain.chain_name}\
        {protocol_s}{src_s}{dst_s}{sport_s}{dport_s}\
        {in_interface_s}{to_source_s}{to_destination_s}{to_port_s}{comment_s}{target_s}'

    class Meta:
        db_table = 'config_iptables_rule'
