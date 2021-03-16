# Firewall api reference

所有返回状态参见code字段，0表示成功，1表示错误，具体错误原因为msg内容

## Get


### 服务器基础信息



#### 读取服务器基础信息

```
method: GET
get: /api/serverInfo/basicInfo
response content-type: application/json

response conent:
{
    "code": 0,
    "msg": "success",
    "data": {
        "hostname": "denggb-Lenovo-IdeaPad-Y470\n",
        "running_total_time": "24643.15",
        "system_time": 1614755950.8489187
    }
}

```

返回值解释

| 字段               | 解释           |
| ------------------ | -------------- |
| hostname           | 主机名         |
| running_total_time | 系统运行总时长 |
| system_time        | 系统当前时间   |



### SAR活动性能指标



#### 读取服务器活动性能(SAR)指标

```
method: GET
get: /api/serverInfo/sar/<resource_object>[?time_range=20s]
example: /api/serverInfo/sar/load?time_range=5m(获取5分钟内，所有CPU负载信息)
response content-type: application/json

response content:
{
    "code": 0,
    "msg": "success",
    "data": [
        {
            "block": "sda",
            "io_rs": 0,
            "io_ws": 8000,
            "io_await": 17500,
            "io_util": 32,
            "time": 1614750185
        }
    ]
}

```

请求解释

| 参数          | 必须 | 说明                                                         |
| ------------- | ---- | ------------------------------------------------------------ |
| resource_name | 是   | 请求获取的资源类型名称，可用资源包含io(IO)、net(网络接口)、cpu(CPU)、memory(内存)、tcp(TCP会话)、load(系统负载) |
| time_range    | 否   | 获取指定时间范围内的活动性能，例如 5m 表示5分钟内的所有数据，不指定该参数则获取最新的一条记录 |

返回值解释

##### io

| 字段     | 说明       |
| -------- | ---------- |
| block    | 块设备名称 |
| io_rs    | 每秒读次数 |
| io_ws    | 每秒写资料 |
| io_await | 等待时长   |
| io_util  | 设备利用率 |
| time     | 采集时间   |

##### load

| 字段   | 说明       |
| ------ | ---------- |
| load1  | 1秒内负载  |
| load5  | 5秒内负载  |
| load15 | 15秒内负载 |
| time   | 采集时间   |

##### mem

| 字段      | 说明                 |
| --------- | -------------------- |
| mem_total | 内存总量（字节）     |
| mem_free  | 内存剩余量（字节）   |
| mem_used  | 内存已用量（字节）   |
| mem_buff  | 内存BUFF用量（字节） |
| mem_util  | 内存利用率（百分比） |
| mem_cache | 内存cache量（字节）  |
| time      | 采集时间             |

##### cpu

| 字段      | 说明                             |
| --------- | -------------------------------- |
| cpu_user  | cpu用户利用率，百分比需要除以100 |
| cpu_sys   | cpu系统利用率，百分比需要除以100 |
| cpu_wait  | CPU等待                          |
| cpu_steal | cpu steal                        |
| cpu_idle  | cpu空闲率，百分比需要除以100     |
| cpu_util  | cpu总利用率                      |
| time      | 采集时间                         |

##### net

| 字段        | 说明       |
| ----------- | ---------- |
| interface   | 接口名称   |
| in_bytes    | 入字节数   |
| in_packets  | 入数据包数 |
| in_errors   | 入错误包   |
| in_drops    | 入丢包数量 |
| out_bytes   | 出字节     |
| out_packets | 出数据包   |
| out_errors  | 出错误     |
| out_drops   | 出丢包     |
| time        | 采集时间   |

##### tcp session

| 字段            | 说明              |
| --------------- | ----------------- |
| tcp_active      | tcp主动向外连次数 |
| tcp_passive     | tcp被动连接次数   |
| tcp_inseg       | tcp in segments   |
| tcp_outseg      | tcp out segments  |
| tcp_established | tcp已建立会话数   |
| tcp_retrans     | tcp重传次数       |
| time            | 采集时间          |



#### 写入服务器活动性能(SAR)指标至数据库

WEB用户无需使用该功能

```
method: POST
post: /api/serverInfo/sar/<resource_object>
request content-type: application/json
response content-type: application/json

request body:
{
	"load1": 1.0,
	"load5": 0.6,
	"load15": 0.5,
	"time:": 1614750185
}

response:
{
	"code": 0,
	"name": "load"
	"message": "success"
}

```

| 参数          | 必须 | 说明                                                         |
| ------------- | ---- | ------------------------------------------------------------ |
| resource_name | 是   | 请求获取的资源名称，可用资源包含io(IO)、net(网络接口)、cpu(CPU)、memory(内存)、tcp(TCP会话)、load(系统负载) |

*具体POST报文格式参见对应的资源模型*

*该方法可以配置允许访问的主机，在collect模块的ALLOW_POST_HOSTS全局变量中修改*



### IP与路由



#### 读取系统静态路由表

```
method: GET
get: /api/serverInfo/ipRoute/getStaticRouteTable[?interface_index=1]
return content-type: application/json

response:
{
    "code": 0,
    "msg": "success",
    "data": [
        {
            "iface": "wlp8s0b1",
            "destination": "0.0.0.0",
            "gateway": "192.168.3.1",
            "netmask": "0.0.0.0",
            "prefix": 0,
            "metric": "600"
        },
        {
            "iface": "wlp8s0b1",
            "destination": "169.254.0.0",
            "gateway": "0.0.0.0",
            "netmask": "255.255.0.0",
            "prefix": 16,
            "metric": "1000"
        },
        {
            "iface": "wlp8s0b1",
            "destination": "192.168.3.0",
            "gateway": "0.0.0.0",
            "netmask": "255.255.255.0",
            "prefix": 24,
            "metric": "600"
        }
    ]
}
```

请求参数

| 字段        | 可选 | 说明                   |
| ---------- | --- | -----------------|
| interface_index | 否 | 网卡接口索止编号           |


返回值解释

| 字段        | 说明                   |
| ----------- | ---------------------- |
| iface       | 网卡接口名称           |
| destination | 目标网段               |
| gateway     | 网关                   |
| netmask     | 子网掩码               |
| prefix      | 前缀（由掩码换算而来） |
| metric      | 优先级                 |



#### 读取网络接口列表

```
method: get
get: /api/serverInfo/interface/getInterfaceList
response content-type: application/json

response:
{
    "code": 0,
    "msg": "success",
    "data": [
        {
            "ifname": "wlp8s0b1",
            "state": "up",
            "index": 1
        },
        {
            "device": "enp7s0",
            "state": "unknow",
            "index": 2
        },
        {
            "device": "lo",
            "state": "unknow",
            "index": 3
        }
    ]
}
```

返回值解释

| 字段       | 说明         |
| ---------- | ------------ |
| ifname     | 网卡接口名称 |
| state      | 接口状态 UP,DOWN,UNKNOW     |
| index      | 接口索引，查询指定路由表时可以指定该参数     |



#### 读取接口详细信息

```
method: get
get: /api/serverInfo/interface/getInterfaceDetail[?ifname=wlp8s0b1]
response content-type: application/json

response:
{
    "code": 1,
    "msg": "success",
    "data": [
        {
            "address": "127.0.0.1",
            "broadcast": null,
            "ifname": "lo",
            "prefix": 8,
            "index": 1
        },
        {
            "address": "192.168.3.161",
            "broadcast": "192.168.3.255",
            "ifname": "wlp8s0b1",
            "prefix": 24,
            "index": 2
        }
    ]
}
```

请求说明

| 参数        | 必选 | 说明         |
| ----------- | ---- | ---------- |
| ifname | 否   | 网卡接口名称，根据网卡接口名称查询对应接口的详细信息 |

返回值解释

| 字段              | 说明                      |
| ---------------- | ------------------------ |
| address     | 接口地址                        |
| broadcast   | 广播地址                        |
| ifname      | 接口名称                        |
| prefix      | 前缀长度                        |
| index      | 网卡接口索引                        |



### Iptables



#### 查询链组

```text
method: GET
get: /api/config/iptables/getChainGroups?group_type=<grou_type>
response content-type: application/json

response:
{
	"code": 0,
	"msg": "success",
	"data":[
		"a","b"
	]
}
```

请求参数

| 参数       | 必选 | 说明                                    |
| ---------- | ---- | --------------------------------------- |
| group_type | 是   | 链组类型，可选类型为snat, dnat, forward |



## Config



### IP与路由



#### 设置接口状态

```text
method: POST
post: /api/config/interface/setInterface
response content-type: application/json

request:
{
    "ifname": "lo",
    "status": "up"
}

response:
{
    "code": 0,
    "msg": "error reason"
}

```
请求说明

| 参数        | 必选 | 说明         |
| ----------- | ---- | ---------- |
| ifanme | 是   | 接口名称 |
| status | 是   | 接口状态 |

#### 配置接口IP地址

```text
method: POST
post: /api/config/ipRoute/setAddress

request body:
{
    "ip": "192.168.100.2",
    "netmask": "255.255.255.0",
    "ifname": "eth0"
}

success:
{
    "code": 0,
    "msg": "success"
}

faild:
{
    "code": 1,
    "msg": "error reason"
}
```

请求说明

| 参数        | 必选 | 说明         |
| ----------- | ---- | ---------- |
| ip | 是   | IP地址 |
| netmask | 是   | 子网掩码，支持前缀格式 |
| ifname | 是   | 接口名称 |



#### 配置路由

```text
method: POST
post: /api/config/ipRoute/setRoute
response content-type: application/json

request body:
{
    "dst": "192.168.100.0/24",
    "gateway": "192.168.3.1",
    "ifname": "eth0"
}

success:
{
    "code": 0,
    "msg": "success"
}

faild:
{
    "code": 1,
    "msg": "error reason"
}
```
请求说明

| 参数        | 必选 | 说明         |
| ----------- | ---- | ---------- |
| dst | 是   | 目标网段 |
| gateway | 是   | 网关地址 |
| ifname | 是   | 接口名称 |
| table | 否   | 是否时写入默认路由表，值为"main"时写入默认路由表，否则写入以接口ID为索引的路由表|



#### 配置策略路由

```text
method: POST
post: /api/config/ipRoute/setPolicyRoute
response content-type: application/json

request body:
{
    "dst": "192.168.100.1/32",
    "ifname": "eth0"
}

success: 
{
    "code": 0,
    "msg": 'success'
}

faild:
{
    "code": 1,
    "msg": 'error reason'
}
```

请求说明

| 参数        | 必选 | 说明         |
| ----------- | ---- | ---------- |
| dst | 否   | 目标地址，格式为192.168.100.0/24或192.168.100.0 |
| dst | 否   | 源地址，格式为192.168.100.0/24或192.168.100.0 |
| src_len | 否 | 源地址掩码长度，如果源标地址，采用网段/前缀格式，则该字段可以省略 |
| dst_len | 否 | 目标地址掩长度，如果目标地址标，采用网段/前缀格式，则该字段可以省略 |
| priority | 否 | 规则优先级 |
| ifname | 是 | 接口名称,将该规则写入对应的接口索引路由表 |
| iifname | 否 | 如果目标网段采用网段/前缀格式，则该字段可以省略 |
| tos | 否 | 服务类型type of service |

>以上所有非必选字段，必须任选其一



### Iptables



#### 添加链组

```text
method: POST
post: /api/config/iptables/setChainGroup
request content-type: application/json

req:
{
	"table_name":"nat",
	"chain_name": "abcdefg",
	"nat_mode": "snat"
}

response:
{
	"code":0,
	"msg": "success"
}
```

请求说明

| 字段       | 必选 | 说明                                                         |
| ---------- | ---- | ------------------------------------------------------------ |
| table_name | 是   | 链组类型，可选值为snat(NAT规则),dnat(端口映射), filter(转发规则) |
| chain_name | 是   | 链组名称，用户自定义链组名称                                 |
| nat_mode   | 否   | 当table_name字段为nat时，该字段变为必选，可选值为(snat, dnat) |



#### 设置端口映射

```text
method: POST
post: /api/config/iptables/setRule/dnat
request content-type: application/json
response content-type: application/json

req:
{
	"chain_group_name": "dnat-test",
	"src": "192.168.3.100/32",
	"dst": "192.168.3.1/32",
	"protocol": "tcp",
	"target": "DNAT",
	"to_destination": "192.168.3.1"
}

response:
{
	"code":0,
	"msg": 'success'
}
```

请求说明

| 字段             | 必选 | 说明                                                         |
| ---------------- | ---- | ------------------------------------------------------------ |
| chain_group_name | 是   | 链组名称，通过api接口查询得到，group_type=snat(查询参数)     |
| src              | 否   | 源地址，格式为 a.b.c.d/prefixlen                             |
| dst              | 否   | 目标地址，格式为 a.b.c.d/prefixlen                           |
| protocol         | 否   | 协议，目前仅支持tcp,udp, 当指定dport,sport参数后，该字段为必选 |
| sport            | 否   | 源端口                                                       |
| dport            | 否   | 目标端口                                                     |
| in_interface     | 否   | 流量入接口名称，通过api可询得到                              |
| to_port          | 否   | 转发目标端口，当target为REDIRECT是，该值为必选               |
| to_destination   | 否   | DNAT模式下使用的目标地址，当target为DNAT时，该值为必选，格式为 a.b.c.d或a.b.c.d/prefixlen |
| comment          | 否   | 规则注释                                                     |
| target           | 是   | 目标，该API接口下，值为DNAT，REDIRECT                        |



#### 设置NAT规则

```text
method: POST
post: /api/config/iptables/setRule/snat
request content-type: application/json
response content-type: application/json

req:
{
	"chain_group_name": "aaa",
	"src": "192.168.3.100/32",
	"dst": "192.168.3.1/32",
	"protocol": "tcp",
	"target": "SNAT",
	"to_source": "192.168.3.1"
}

response:
{
	"code":0,
	"msg": 'success'
}
```

请求说明

| 字段             | 必选 | 说明                                                         |
| ---------------- | ---- | ------------------------------------------------------------ |
| chain_group_name | 是   | 链组名称，通过api接口查询得到，group_type=snat(查询参数)     |
| src              | 否   | 源地址，格式为 a.b.c.d/prefixlen                             |
| dst              | 否   | 目标地址，格式为 a.b.c.d/prefixlen                           |
| protocol         | 否   | 协议，目前仅支持tcp,udp, 当指定dport,sport参数后，该字段为必选 |
| sport            | 否   | 源端口                                                       |
| dport            | 否   | 目标端口                                                     |
| in_interface     | 否   | 流量入接口名称，通过api可询得到                              |
| to_source        | 否   | NAT源地址，当target为SNAT时，该值为必选                      |
| comment          | 否   | 规则注释                                                     |
| target           | 是   | 目标，该该API接口下，值为SNAT，MASQUERADE                    |



#### 设置转发规则

#### 

```text
method: POST
post: /api/config/iptables/setRule/filter
request content-type: application/json
response content-type: application/json

req:
{
	"chain_group_name": "aaa",
	"src": "192.168.3.100/32",
	"dport": 80,
	"protocol": "tcp",
	"target": "ACCEPT",
}

response:
{
	"code":0,
	"msg": 'success'
}
```

请求说明

| 字段             | 必选 | 说明                                                         |
| ---------------- | ---- | ------------------------------------------------------------ |
| chain_group_name | 是   | 链组名称，通过api接口查询得到，group_type=snat(查询参数)     |
| src              | 否   | 源地址，格式为 a.b.c.d/prefixlen                             |
| dst              | 否   | 目标地址，格式为 a.b.c.d/prefixlen                           |
| protocol         | 否   | 协议，目前仅支持tcp,udp, 当指定dport,sport参数后，该字段为必选 |
| sport            | 否   | 源端口                                                       |
| dport            | 否   | 目标端口                                                     |
| comment          | 否   | 规则注释                                                     |
| in_interface     | 否   | 流量入接口名称，通过api可询得到                              |
| target           | 是   | 目标，该该API接口下，值为ACCEPT(接收),DROP(丢弃)             |





## Delete



### IP与路由



#### 删除接口IP地址

 >参考设置API，请求方法为DELETE



#### 删除静态路由

 >参考设置API,请求方法为DELETE

#### 删除策略路由

 >参考设置API,请求方法为DELETE



#### 清理前一天前的所有sar采集数据

WEB界面暂不需要读取

```
method: GET
get: /api/serverInfo/sarClear
response content-type: application/json


{
    "code": 0,
    "msg": "success"
}
```

