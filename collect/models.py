from django.db import models


# Create your models here.


class SysLoad(models.Model):
    """
    collect system load
    """
    load1 = models.FloatField(verbose_name="load1", blank=False, null=False)
    load5 = models.FloatField(verbose_name="load5", blank=False, null=False)
    load15 = models.FloatField(verbose_name="load15", blank=False, null=False)
    time = models.IntegerField(verbose_name="datetime", blank=False, null=False)

    def __str__(self):
        return 'load1:%s, load5:%s, load15:%s' % (self.load1, self.load5, self.load15)

    class Meta:
        verbose_name = 'system load'
        db_table = 'collect_sys_load'
        ordering = ["-time"]


class MemoryInfo(models.Model):
    mem_total = models.IntegerField(verbose_name="mem total", blank=False, null=False)
    mem_free = models.IntegerField(verbose_name="mem free", blank=False, null=False)
    mem_used = models.IntegerField(verbose_name="mem used", blank=False, null=False)
    mem_buff = models.IntegerField(verbose_name="mem buff", blank=False, null=False)
    mem_util = models.FloatField(verbose_name="mem util", blank=False, null=False)
    mem_cache = models.IntegerField(verbose_name="mem cache", blank=False, null=False)
    time = models.IntegerField(verbose_name="datetime", blank=False, null=False)

    def __str__(self):
        return f"total:{self.mem_total}, free:{self.mem_free}, used:{self.mem_used}," \
               f"buff:{self.mem_buff}, util:{self.mem_util}, cache:{self.mem_cache},"

    class Meta:
        verbose_name = "memory info"
        db_table = "collect_mem_info"
        ordering = ["time"]


class CpuInfo(models.Model):
    cpu_user = models.IntegerField(verbose_name="cpu_user", blank=False, null=False)
    cpu_sys = models.IntegerField(verbose_name="cpu_sys", blank=False, null=False)
    cpu_wait = models.IntegerField(verbose_name="cpu_wait", blank=False, null=False)
    cpu_steal = models.IntegerField(verbose_name="cpu_steal", blank=False, null=False)
    cpu_idle = models.IntegerField(verbose_name="cpu_idle", blank=False, null=False)
    cpu_util = models.IntegerField(verbose_name="cpu_util", blank=False, null=False)
    time = models.IntegerField(verbose_name="datetime", blank=False, null=False)

    def __str__(self):
        return f"cpu_user:{self.cpu_user}, cpu_sys:{self.cpu_sys}, cpu_idle:{self.cpu_idle}, cpu_util:{self.cpu_util}"

    class Meta:
        verbose_name = "cpu info"
        db_table = "collect_cpu_info"
        ordering = ["time"]


class IoInfo(models.Model):
    block = models.CharField(verbose_name="block device name", max_length=50, null=False, blank=False)
    io_rs = models.IntegerField(verbose_name="io read second", blank=False, null=False)
    io_ws = models.IntegerField(verbose_name="io write second", blank=False, null=False)
    io_await = models.IntegerField(verbose_name="io await", blank=False, null=False)
    io_util = models.IntegerField(verbose_name="io utilization", blank=False, null=False)
    time = models.IntegerField(verbose_name="datetime", blank=False, null=False)

    def __str__(self):
        return f"block:{self.block}, io_rs:{self.io_rs}, io_ws:{self.io_ws}, \
        io_await:{self.io_await}, io_util:{self.io_util}"

    class Meta:
        verbose_name = "block device io info"
        db_table = "collect_io_info"
        ordering = ["time"]


class NetInfo(models.Model):
    interface = models.CharField(verbose_name="interface name", max_length=50, null=False, blank=False)
    in_bytes = models.IntegerField(verbose_name="in bytes", blank=False, null=False)
    in_packets = models.IntegerField(verbose_name="in packets", blank=False, null=False)
    in_errors = models.IntegerField(verbose_name="in errors", blank=False, null=False)
    in_drops = models.IntegerField(verbose_name="in drops", blank=False, null=False)
    out_bytes = models.IntegerField(verbose_name="out bytes", blank=False, null=False)
    out_packets = models.IntegerField(verbose_name="out packets", blank=False, null=False)
    out_errors = models.IntegerField(verbose_name="out errors", blank=False, null=False)
    out_drops = models.IntegerField(verbose_name="out drops", blank=False, null=False)
    time = models.IntegerField(verbose_name="datetime", blank=False, null=False)

    def __str__(self):
        return f"interface:{self.interface}, in_bytes:{self.in_bytes}, out_bytes:{self.out_bytes}"

    class Meta:
        verbose_name = "net info"
        db_table = "collect_net_info"
        ordering = ["time"]


class TcpInfo(models.Model):
    tcp_active = models.IntegerField(verbose_name="tcp active", blank=False, null=False)
    tcp_passive = models.IntegerField(verbose_name="tcp passive", blank=False, null=False)
    tcp_inseg = models.IntegerField(verbose_name="tcp in seq", blank=False, null=False)
    tcp_outseg = models.IntegerField(verbose_name="tcp out seq", blank=False, null=False)
    tcp_established = models.IntegerField(verbose_name="tcp established", blank=False, null=False)
    tcp_retran = models.IntegerField(verbose_name="tcp retransfer", blank=False, null=False)
    time = models.IntegerField(verbose_name="datetime", blank=False, null=False)

    def __str__(self):
        return f"tcp_active:{self.tcp_active}, tcp_passive:{self.tcp_passive}"

    class Meta:
        verbose_name = "tcp session info"
        db_table = "collect_tcp_info"
        ordering = ["time"]
