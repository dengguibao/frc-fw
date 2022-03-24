#! /usr/bin/python3
# SAR (server activity report)
import time
import threading
import queue
import sys
import argparse
import json

if sys.version_info[0] == 2:
    import urllib as request
else:
    from urllib import request


Q = queue.Queue()
SERVER = None
DELAY = 0
LAST_CPU_INFO = LAST_TCP_INFO = LAST_NET_INFO = LAST_IO_INFO = None


def collect_load_avg():
    """
    collect system load
    """
    load_file = open("/proc/loadavg")
    content = load_file.read().split()
    load_file.close()
    if len(content) >= 3:
        return {
            "load1": float(content[0]),
            "load5": float(content[1]),
            "load15": float(content[2]),
            "time": int(time.time())
        }

    return


# ----------------------- mem ------------------------------


def collect_memory_info():
    """
    collect memory info
    """
    memory_buffer = {}
    with open("/proc/meminfo") as mem_file:
        for line in mem_file:
            field_split = line.split(':')
            k = field_split[0].strip()
            v = field_split[1].split()[0].strip()
            memory_buffer[k] = int(v)

    # 过滤只取关注的指标
    mem_total = memory_buffer["MemTotal"]
    mem_free = memory_buffer["MemFree"] + memory_buffer["Buffers"] + memory_buffer["Cached"]
    mem_used = mem_total - mem_free
    mem_util = mem_used/mem_total * 100
    mem_buff = int(float(memory_buffer["Buffers"])/float(mem_total) * 10000)
    mem_cache = int(float(memory_buffer["Cached"])/float(mem_total) * 10000)
    return {
        "mem_total": mem_total,
        "mem_free": mem_free,
        "mem_used": mem_used,
        "mem_buff": mem_buff,
        "mem_util": mem_util,
        "mem_cache": mem_cache,
        "time": int(time.time())
    }


# ----------------------- cpu ------------------------------


def collect_cpu_info():
    """
    collect cpu info
    """
    cpu_buffer = {}
    with open("/proc/stat") as cpu_file:
        for line in cpu_file:
            line_fields = line.split()
            if line_fields[0] == "cpu":
                total = 0
                for field in line_fields:
                    if field == "cpu":
                        continue
                    total += int(field)

                cpu_buffer = {
                    "User": int(line_fields[1]),
                    "Sys": int(line_fields[3]),
                    "Idle": int(line_fields[4]),
                    "Steal": int(line_fields[8]),
                    "Wait": int(line_fields[5]),
                    "Total": total
                }
                break
    return cpu_buffer


def calculate_cpu_info():
    """
    alculate cpu info
    """
    global LAST_CPU_INFO
    cpu_info = collect_cpu_info()
    if LAST_CPU_INFO is None:
        LAST_CPU_INFO = cpu_info
        return {}
    else:
        delta_total = cpu_info["Total"] - LAST_CPU_INFO["Total"]
        delta_user = cpu_info["User"] - LAST_CPU_INFO["User"]
        delta_sys = cpu_info["Sys"] - LAST_CPU_INFO["Sys"]
        delta_idle = cpu_info["Idle"] - LAST_CPU_INFO["Idle"]
        delta_wait = cpu_info["Wait"] - LAST_CPU_INFO["Wait"]
        delta_steal = cpu_info["Steal"] - LAST_CPU_INFO["Steal"]
        LAST_CPU_INFO = cpu_info
        return {
            "cpu_user": int(float(delta_user)/float(delta_total) * 10000),
            "cpu_sys": int(float(delta_sys)/float(delta_total) * 10000),
            "cpu_wait": int(float(delta_wait)/float(delta_total) * 10000),
            "cpu_steal": int(float(delta_steal)/float(delta_total) * 10000),
            "cpu_idle": int(float(delta_idle)/float(delta_total) * 10000),
            "cpu_util": int(float(delta_total - delta_idle - delta_wait - delta_steal)/float(delta_total) * 100),
            "time": int(time.time())
        }


# ------------------------ io ------------------------------


def should_handle_device(device):
    """
    define collect block
    """
    normal = len(device) == 3 and device.startswith("sd") or device.startswith("vd")
    aws = len(device) >= 4 and device.startswith("xvd") or device.startswith("sda")
    return normal or aws


def collect_io_info():
    """
    collect io info
    """
    io_buffer = {}
    with open("/proc/diskstats") as io_file:
        for line in io_file:
            line_fields = line.split()
            device_name = line_fields[2]
            if line_fields[3] == "0":
                continue
            if should_handle_device(device_name):
                io_buffer[device_name] = {
                    "ReadRequest": int(line_fields[3]),
                    "WriteRequest": int(line_fields[7]),
                    "MsecRead": int(line_fields[6]),
                    "MsecWrite": int(line_fields[10]),
                    "MsecTotal": int(line_fields[12]),
                    "Timestamp": int(time.time())
                }
    return io_buffer


def calculate_io_info():
    """
    calculate io
    """
    global LAST_IO_INFO
    io_info = collect_io_info()
    result = []
    if LAST_IO_INFO:
        for key in io_info.keys():
            total_duration = io_info[key]["Timestamp"] - LAST_IO_INFO[key]["Timestamp"]
            read_use_io = io_info[key]["MsecRead"] - LAST_IO_INFO[key]["MsecRead"]
            write_use_io = io_info[key]["MsecWrite"] - LAST_IO_INFO[key]["MsecWrite"]
            read_io = io_info[key]["ReadRequest"] - LAST_IO_INFO[key]["ReadRequest"]
            write_io = io_info[key]["WriteRequest"] - LAST_IO_INFO[key]["WriteRequest"]
            read_write_io = io_info[key]["MsecTotal"] - LAST_IO_INFO[key]["MsecTotal"]
            readwrite_io = read_io + write_io
            io_awit = 0
            if readwrite_io > 0:
                io_awit = int(float(read_use_io + write_use_io) / float(readwrite_io) * 10000)
            result.append({
                'block': key,
                "io_rs": int((read_io/total_duration) * 10000),
                "io_ws": int((write_io/total_duration) * 10000),
                "io_await": io_awit,
                "io_util": int(float(read_write_io) / (total_duration * 1000) * 10000),
                "time": int(time.time())
            })

    LAST_IO_INFO = io_info
    return result


# ----------------------- interface traffic ------------------------------


def should_collect_card(line):
    """
    define collect interface
    """
    return line.startswith("eth") or line.startswith("em") or line.startswith('enp') or line.startswith('ens')


def collect_net_info():
    """
    collect interface traffic
    """
    net_buffer = {}
    with open("/proc/net/dev") as net_file:
        for line in net_file:
            if line.find(":") < 0:
                continue
            card_name = line.split(":")[0].strip()
            if should_collect_card(card_name):
                line_fields = line.split(":")[1].lstrip().split()
                net_buffer[card_name] = {
                    "InBytes": int(line_fields[0]),
                    "InPackets": int(line_fields[1]),
                    "InErrors": int(line_fields[2]),
                    "InDrops": int(line_fields[3]),
                    "OutBytes": int(line_fields[8]),
                    "OutPackets": int(line_fields[9]),
                    "OutErrors": int(line_fields[10]),
                    "OutDrops": int(line_fields[11])
                }
    return net_buffer


def calculate_net_info():
    """
    calculate interface traffic
    """
    global LAST_NET_INFO
    net_info = collect_net_info()
    result = []
    if LAST_NET_INFO is not None:
        for key in net_info.keys():
            result.append({
                "interface": key,
                "in_bytes": (net_info[key]["InBytes"] - LAST_NET_INFO[key]["InBytes"]) * 10000,
                "in_packets": (net_info[key]["InPackets"] - LAST_NET_INFO[key]["InPackets"]) * 10000,
                "in_errors": (net_info[key]["InErrors"] - LAST_NET_INFO[key]["InErrors"]) * 10000,
                "in_drops": (net_info[key]["InDrops"] - LAST_NET_INFO[key]["InDrops"]) * 10000,
                "out_bytes": (net_info[key]["OutBytes"] - LAST_NET_INFO[key]["OutBytes"]) * 10000,
                "out_packets": (net_info[key]["OutPackets"] - LAST_NET_INFO[key]["OutPackets"]) * 10000,
                "out_errors": (net_info[key]["OutErrors"] - LAST_NET_INFO[key]["OutErrors"]) * 10000,
                "out_drops": (net_info[key]["OutDrops"] - LAST_NET_INFO[key]["OutDrops"]) * 10000,
                "time": int(time.time())
            })
    LAST_NET_INFO = net_info
    return result


# ----------------------- session ------------------------------


def collect_tcp_info():
    """
    collect tcp session
    """
    session_buffer = {}
    is_title = True
    with open("/proc/net/snmp") as snmp_file:
        for line in snmp_file:
            protocol_name = line.split(":")[0].strip()
            if protocol_name == "Tcp":
                if is_title:
                    is_title = False
                    continue
                else:
                    line_fields = line.split(":")[1].lstrip().split()
                    session_buffer = {
                        "ActiveOpens": int(line_fields[4]),
                        "PassiveOpens": int(line_fields[5]),
                        "InSegs": int(line_fields[9]),
                        "OutSegs": int(line_fields[10]),
                        "RetransSegs": int(line_fields[11]),
                        "CurrEstab": int(line_fields[8]),
                    }
                    break
    return session_buffer


def calculate_tcp_info():
    """
    calculate tcp session number
    """
    global LAST_TCP_INFO
    session_info = collect_tcp_info()
    result = {}
    if LAST_TCP_INFO is not None:
        outSegsTcp = session_info["OutSegs"] - LAST_TCP_INFO["OutSegs"]
        try:
            retransRate = float(session_info["RetransSegs"] - LAST_TCP_INFO["RetransSegs"])/float(outSegsTcp)
        except:
            retransRate = 0
        result = {
            "tcp_active": (session_info["ActiveOpens"] - LAST_TCP_INFO["ActiveOpens"]) * 10000,
            "tcp_passive": (session_info["PassiveOpens"] - LAST_TCP_INFO["PassiveOpens"]) * 10000,
            "tcp_inseg": (session_info["InSegs"] - LAST_TCP_INFO["InSegs"]) * 10000,
            "tcp_outseg": outSegsTcp * 10000,
            "tcp_established": session_info["CurrEstab"] * 10000,
            "tcp_retran": int(retransRate * 10000),
            "time": int(time.time())
        }
    LAST_TCP_INFO = session_info
    return result


def worker(f):
    """
    worker thread
    """
    while 1:
        result = f()
        f_name = f.__name__.split('_')[1]
        if not result:
            pass
        else:
            Q.put({
                'name': f_name,
                'data': result
            })
        time.sleep(DELAY)


def write_to_db():
    """
    collect result write to database
    :return:
    """
    while 1:
        d = Q.get()
        Q.task_done()
        if not d:
            continue

        if isinstance(d['data'], list):
            for item in d['data']:
                res = post_data({
                    'name': d['name'],
                    'data': item
                })
                console_log(res)
        else:
            res = post_data(d)
            console_log(res)


def console_log(data: dict):
    """
    console print
    :param data:
    :return:
    """
    # data = json.loads(json_str)
    if data and 'name' in data and 'msg' in data:
        print(data['name'], 'write to db', data['msg'])


def post_data(d: dict):
    """
    post data to server
    :param d:
    :return:
    """
    if not isinstance(d, dict) and 'name' not in d and 'data' not in d:
        return

    resource_name = d['name']
    api = f"{SERVER}/api/serverInfo/sar/{resource_name}"

    json_str = json.dumps(d['data'], ensure_ascii=False)
    n = 0

    result = False
    while 1:
        try:
            req = request.urlopen(api, data=json_str.encode())
            if req and req.getcode() in (200, 201, 400):
                result = json.loads(req.read().decode())
        except json.decoder.JSONDecodeError:
            print('json parse failed, origin json ')
        except:
            n += 1
            if n >= 5:
                break
            time.sleep(1)
            print('connect to api server %s is timeout!' % api)
        else:
            break
    return result


if __name__ == '__main__':

    av = sys.argv[1:]
    if not len(av):
        av.append('-h')

    parser = argparse.ArgumentParser(description='system activites info collect program')
    parser.add_argument('--server', type=str, required=True, help='api server address')
    parser.add_argument('--delay', type=int, required=False, help='collector delay seconds, default: 5s', default=5)
    args = parser.parse_args(av)

    DELAY = args.delay
    SERVER = args.server[7:] if args.server.startswith('http://') else 'http://%s' % args.server

    threading.Thread(target=write_to_db).start()
    collect_item = [
        collect_load_avg,
        collect_memory_info,
        calculate_cpu_info,
        calculate_io_info,
        calculate_net_info,
        calculate_tcp_info
    ]
    for i in collect_item:
        t = threading.Thread(target=worker, args=(i,))
        t.start()
