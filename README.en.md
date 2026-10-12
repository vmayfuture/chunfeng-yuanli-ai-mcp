# chunfeng-yuanli-ai-mcp — Local BLE MCP control for DokiDoki DK-META2

[中文](README.md) | [English](README.en.md)

chunfeng-yuanli-ai-mcp is an unofficial local Model Context Protocol (MCP) server for the NetEase Chunfeng / Heartbeat Yuanli DokiDoki `DK-META2` device. An MCP client communicates over stdio; the server uses Bleak and Bluetooth Low Energy (BLE) GATT to control vibration, linear motion and rotation.

This experimental implementation is based on observed client communication. It does not read vendor accounts, call cloud control APIs or bundle official client software or firmware. Product names belong to their owners; there is no vendor affiliation or endorsement.

## Install and diagnose

Requirements: Python 3.11+, BLE-capable OS/hardware, Bluetooth enabled, scanning/connection permissions and an available supported device. Windows is the primary validation environment.

```powershell
git clone https://github.com/vmayfuture/chunfeng-yuanli-ai-mcp.git
cd chunfeng-yuanli-ai-mcp
py -3.11 -m venv .venv
& ./.venv/Scripts/python.exe -m pip install -e .
& ./.venv/Scripts/python.exe -m heartbeat_yuanli_mcp.server --doctor
```

The diagnostic command checks the environment and nearby supported devices. Release competing connections in the official client before connecting through MCP.

## Configure a client

Use the virtual environment's absolute Python path:

```json
{
  "mcpServers": {
    "heartbeat-yuanli": {
      "command": "C:/tools/chunfeng-yuanli-ai-mcp/.venv/Scripts/python.exe",
      "args": ["-m", "heartbeat_yuanli_mcp.server"],
      "env": {"DOKIDOKI_DEVICE_NAME": "DK-META2"}
    }
  }
}
```

Replace the path with your installation path. Other systems use their corresponding interpreter. Entry points are `heartbeat-yuanli-mcp` and `python -m heartbeat_yuanli_mcp.server`. See [configuration example](mcp-config.example.json) and [Chinese guide](README.md).

## First use

Stay beside the device and retain a physical way to stop it. Example agent requests:

```text
Use heartbeat-yuanli to list supported nearby devices. Report the list only;
do not send motion commands.
```

```text
Connect the DK-META2 device I selected. Read its connection status,
verify stop_device first, then disconnect.
```

These are sample prompts, not new hardware test results. An explicitly authorized low-intensity test can use:

```text
list_devices
connect_device
set_vibration(level=20, confirm=true)
stop_device
disconnect_device
```

| Tool | Behavior |
| --- | --- |
| `list_devices` | Scan supported devices; no motion |
| `connect_device` | Connect and discover GATT capabilities |
| `get_device_status` | Report MCP's connection state |
| `set_vibration` | Vibration level, 0–100 |
| `set_linear` | Linear motion level, 0–100 |
| `set_rotary` | Rotation level, 0–100 |
| `stop_device` | Set supported outputs to zero |
| `disconnect_device` | Stop heartbeat, zero outputs and disconnect |

Nonzero motion requires `confirm=true`. This is a local gate, not Bluetooth authentication. Connection state does not prove actual physical output; observe it directly. Arbitrary GATT writes, command codes and raw hexadecimal commands are not exposed.

## Compatibility and limits

Only the `DK-META2` profile is implemented and currently validated. Recognizing names beginning with `TF-`, `DK-` or `TRYFUN-` does not establish another model's compatibility.

A heartbeat is sent every two seconds after connection. Heartbeat/write failures, shutdown and explicit disconnect trigger attempts to stop supported outputs and disconnect. These actions depend on the OS, BLE link and firmware. Do not run nonzero motion unattended or when device state and a quick stop are uncertain.

The official client and MCP should not hold the same GATT connection simultaneously. Vendor account authentication, encrypted pairing implementation and cloud authorization are not included. Commands send one frame per action with no additional 120 ms application throttle; frequent calls need hardware stability checks.

## Protocol and tests

The profile uses service `0000ffac-0000-1000-8000-00805f9b34fb`, write characteristics `ffb5` / `ffb7`, and notification characteristic `ffb8`. Vibration, linear motion and rotation use `0x08`, `0x0B` and `0x0E`. See [protocol notes](docs/protocol.md).

```powershell
& ./.venv/Scripts/python.exe -m unittest discover -s tests -v
```

Pure protocol construction tests need no hardware; they do not establish real BLE compatibility. Hardware checks should begin at low intensity and verify stopping first.

**Cannot connect?** Check permissions, proximity and battery, release competing connections and run `--doctor`.

**Does it use the cloud?** Control runs locally over BLE without vendor account access.

**Can I use another model?** A matching prefix is insufficient; a profile and live validation are needed.

MIT license: [LICENSE](LICENSE). Contributions: [CONTRIBUTING.md](CONTRIBUTING.md). Security or unexpected behavior: [SECURITY.md](SECURITY.md).
