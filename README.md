# 网易春风 · 心跳元力｜使用 AI 控制你的设备

让 AI 成为你的设备秘书：通过自然语言和本地 Bluetooth Low Energy（BLE），控制心跳元力 DokiDoki `DK-META2` 设备的震动、伸缩与旋转。

这是一个非官方、本地优先的 MCP 实现，主打隐私、低延迟和可控的设备操作。

本项目是非官方实现，不读取账号、不调用云端控制接口，也不包含官方客户端源码、安装包或设备固件。DokiDoki、心跳元力及相关名称归其各自权利人所有；本项目与设备厂商没有隶属或背书关系。

> 状态：实验性项目。协议和设备行为来自对客户端通信行为的观察，使用前请在场确认设备状态，并保留实体停止方式。

## 工作原理

MCP 只是 AI 客户端与本地工具之间的调用协议，真正的设备通信链路如下：

```text
MCP 客户端
    │ JSON-RPC / stdio
    ▼
heartbeat_yuanli_mcp.server
    │ 工具参数校验与生命周期管理
    ▼
DokiDokiDeviceManager
    │ Bleak
    ▼
Windows Bluetooth LE
    │ GATT service/characteristic 写入
    ▼
DK-META2
```

当前只实现 `DK-META2` profile：

| 能力 | 命令码 |
| --- | --- |
| 震动 | `0x08` |
| 伸缩 | `0x0B` |
| 旋转 | `0x0E` |

## 要求

- Python 3.11 或更高版本；
- 支持 BLE 的操作系统，Windows 是当前主要验证环境；
- 系统蓝牙已开启，设备没有被官方客户端或其他程序独占；
- 对应系统账户具有蓝牙扫描和连接权限。

## 安装

```powershell
py -3.11 -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -e .
```

检查运行环境和附近支持的设备：

```powershell
& .\.venv\Scripts\python.exe -m heartbeat_yuanli_mcp.server --doctor
```

## 启动 MCP 服务

标准 MCP 客户端需要启动以下命令，并通过 stdio 与其通信：

```text
python -m heartbeat_yuanli_mcp.server
```

也可以使用安装后的入口命令：

```text
heartbeat-yuanli-mcp
```

配置示例见 [mcp-config.example.json](./mcp-config.example.json)。如果需要固定设备，可以通过环境变量设置自己的设备名或蓝牙地址；公开仓库不会保存真实设备地址。

## MCP 工具

| 工具 | 作用 |
| --- | --- |
| `list_devices` | 扫描并列出支持的 BLE 设备，不发送动作 |
| `connect_device` | 连接设备并发现 GATT 能力 |
| `get_device_status` | 查看 MCP 自己持有的连接状态 |
| `set_vibration` | 设置震动强度，范围 `0–100` |
| `set_linear` | 设置伸缩强度，范围 `0–100` |
| `set_rotary` | 设置旋转强度，范围 `0–100` |
| `stop_device` | 将所有已支持输出归零 |
| `disconnect_device` | 停止心跳、归零输出并断开连接 |

典型调用顺序：

```text
list_devices
connect_device
set_vibration(level=20, confirm=true)
set_linear(level=20, confirm=true)
set_rotary(level=20, confirm=true)
stop_device
disconnect_device
```

非零动作必须显式传入 `confirm=true`。确认参数只是本地安全门槛，不是设备的蓝牙认证机制。当前 MCP 不提供任意特征、任意命令码或原始十六进制写入工具。

## BLE 协议概览

设备使用以下 GATT 能力：

```text
Service:                 0000ffac-0000-1000-8000-00805f9b34fb
Write with response:     ffb5
Write without response:  ffb7
Notify:                  ffb8
```

一个普通控制帧为：

```text
[message_id] [0x02] [0x00] [length] [command] [value] [checksum]
```

例如震动强度 20：

```text
01 02 00 03 08 14 E4
```

其中 `0x14` 是十进制 20，校验和只覆盖 `[command, value]`：

```text
checksum = (-(command + value)) & 0xFF
```

完整说明见 [docs/protocol.md](./docs/protocol.md)。

## 安全与已知限制

- 连接成功后每两秒发送一次心跳；心跳或写入失败时会尝试停止输出并断开；
- MCP 退出、显式断开和停止操作都会尝试把支持的输出归零；
- 官方心跳元力客户端和 MCP 不应同时持有同一个 GATT 连接。连接失败时先在官方客户端中断开设备；
- 当前只验证 `DK-META2`。虽然扫描器识别若干 `TF-`、`DK-`、`TRYFUN-` 前缀，但其他型号不会因为名称匹配就自动获得兼容性；
- BLE 连接本身依赖操作系统权限和设备固件行为，本项目不实现厂商账号认证、加密配对或云端授权；
- 协议层当前按单动作发送一帧，快速连续调用没有额外的 120ms 应用层节流。需要高频控制时请先在实际设备上验证稳定性。

请勿在无人看护、无法快速停止或不清楚设备当前状态时运行非零动作。

## 开发与测试

```powershell
& .\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

协议构造函数是纯函数，可以在没有蓝牙设备的环境中测试。实机测试应从低强度开始，并先验证 `stop_device`。

## 许可证

本项目使用 MIT License，见 [LICENSE](./LICENSE)。依赖包各自遵循其上游许可证。

## 贡献

提交问题或改动前请阅读 [CONTRIBUTING.md](./CONTRIBUTING.md)。涉及安全、设备异常动作或潜在隐私泄露的问题，请优先阅读 [SECURITY.md](./SECURITY.md)。
