# API reference

所有返回状态参见code字段，0表示成功，1表示错误，具体错误原因为msg内容

## Get 



#### 读取服务器基础信息

```
method: GET
get: /api/server/basicInfo
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



#### 获取服务器活动性能(SAR)指标

```
method: GET
get: /api/server/sar/<resource_object>[?time_range=20s]
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
| resource_name | 是   | 请求获取的资源名称，可用资源包含io(IO)、net(网络接口)、cpu(CPU)、memory(内存)、tcp(TCP会话)、load(系统负载) |
| time_range    | 否   | 获取指定时间范围内的活动性能，例如 5m 表示5分钟内的所有数据，不指定该参数则获取最新的一条记录 |

返回值解释

| 字段     | 说明       |
| -------- | ---------- |
| block    | 块设备名称 |
| io_rs    | 每秒读次数 |
| io_ws    | 每秒写资料 |
| io_await | 等待时长   |
| io_util  | 设备利用率 |
| time     | 采集时间   |



#### 写入服务器活动性能(SAR)指标至数据库

WEB用户无需使用该功能

```
method: POST
post: /api/server/sar/<resource_object>
request content-type: application/json
response content-type: application/json

request body:
{
	"load1": 1.0,
	"load5": 0.6,
	"load15": 0.5,
	"time:": 1614750185
}

response content:
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



#### 读取系统静态路由表

```
method: GET
get: /api/server/ipRoute/getStaticRouteTable
return content-type: application/json


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

返回值解释

| 字段        | 说明                   |
| ----------- | ---------------------- |
| iface       | 网卡接口名称           |
| destination | 目标网段               |
| gateway     | 网关                   |
| netmask     | 子网掩码               |
| prefix      | 前缀（由掩码换算而来） |
| metric      | 跃点数                 |



#### 读取网络接口列表

```
method: get
get: /api/server/ipRoute/getInterfaceList
response content-type: application/json


{
    "code": 0,
    "msg": "success",
    "data": [
        {
            "device": "wlp8s0b1",
            "type": "wifi",
            "state": "connected",
            "connection": "展示2楼办公室"
        },
        {
            "device": "enp7s0",
            "type": "ethernet",
            "state": "unavailable",
            "connection": "--"
        },
        {
            "device": "lo",
            "type": "loopback",
            "state": "unmanaged",
            "connection": "--"
        }
    ]
}
```

返回值解释

| 字段       | 说明         |
| ---------- | ------------ |
| device     | 网卡接口名称 |
| type       | 接口类型     |
| state      | 接口状态     |
| connection | 接口链接名称 |



#### 根据接口名称读取接口详细信息

```
method: get
get: /api/server/ipRoute/getInterfaceDetail?<device_name=wlp8s0b1>
response content-type: application/json

{
    "code": 0,
    "msg": "success",
    "data": {
        "GENERAL.DEVICE": "wlp8s0b1",
        "GENERAL.TYPE": "wifi",
        "GENERAL.HWADDR": "08:ED:B9:9F:C2:B5",
        "GENERAL.MTU": "1500",
        "GENERAL.STATE": "100",
        "GENERAL.CONNECTION": "展示2楼办公室",
        "GENERAL.CON-PATH": "/org/freedesktop/NetworkManager/ActiveConnection/1",
        "IP4.ADDRESS[1]": "192.168.3.161/24",
        "IP4.GATEWAY": "192.168.3.1",
        "IP4.ROUTE[1]": "dst",
        "IP4.ROUTE[2]": "dst",
        "IP4.ROUTE[3]": "dst",
        "IP4.DNS[1]": "192.168.3.1",
        "IP6.ADDRESS[1]": "fe80::8033:7c4f:40d7:d9eb/64",
        "IP6.GATEWAY": "--",
        "IP6.ROUTE[1]": "dst",
        "IP6.ROUTE[2]": "dst",
        "IP6.ROUTE[3]": "dst"
    }
}
```

请求说明

| 参数        | 必选 | 说明                                                 |
| ----------- | ---- | ---------------------------------------------------- |
| device_name | 是   | 网卡接口名称，根据网卡接口名称查询对应接口的详细信息 |

返回值解释

该返回值不需要全部使用

| 字段              | 说明                                                        |
| ----------------- | ----------------------------------------------------------- |
| GENRAL.DEVICE     | 网卡接口名称                                                |
| GENRAL.TYPE       | 接口类型                                                    |
| GENRAL.HWADDR     | 网卡的MAC地址，即物理地址                                   |
| GENRAL.MTU        | 网卡的MTU，即最大传送单元                                   |
| GENRAL.STATE      | 网卡的连接速率，100代表100M                                 |
| GENRAL.CONNECTION | 网卡所用的网络连接                                          |
| IP4.ADDRESS[1]    | 网卡的IPV4地址，[1]表示第一个IP，一张网卡可以配置多个IP地址 |
| IP4.GATEWAY       | 网卡的IPV4网关                                              |
| IP6.ADDRESS[1]    | 网卡的IPV6地址                                              |



## Config









## Delete

#### 清理前一天前的所有sar采集数据

WEB界面暂不需要读取

```
method: GET
get: /api/server/sarClear
response content-type: application/json


{
    "code": 0,
    "msg": "success"
}
```

