"""MCP stdio server for direct control of the connected DokiDoki device."""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import sys
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

from mcp.server.mcpserver import Context, MCPServer

from .device_manager import DokiDokiDeviceManager, DokiDokiError

LOGGER = logging.getLogger("heartbeat_yuanli_mcp")


@dataclass
class AppContext:
    manager: DokiDokiDeviceManager


@contextlib.asynccontextmanager
async def app_lifespan(_server: MCPServer) -> AsyncIterator[AppContext]:
    manager = DokiDokiDeviceManager()
    try:
        yield AppContext(manager=manager)
    finally:
        await manager.shutdown()


mcp = MCPServer(
    name="heartbeat-yuanli-mcp",
    title="心跳元力 BLE MCP",
    version="0.1.0",
    description="通过本地 Bluetooth LE 调用已授权的心跳元力 DokiDoki 设备。",
    instructions=(
        "先调用 get_device_status 或 list_devices，再调用 connect_device。"
        "非零动作必须显式传 confirm=true；停止操作使用 stop_device。"
    ),
    lifespan=app_lifespan,
    log_level="WARNING",
)


def _manager(ctx: Context) -> DokiDokiDeviceManager:
    if ctx.request_context is None:
        raise RuntimeError("MCP 请求上下文不可用。")
    return ctx.request_context.lifespan_context.manager


def _error_result(exc: Exception) -> dict[str, Any]:
    if isinstance(exc, DokiDokiError):
        code = exc.code
    elif isinstance(exc, ValueError):
        code = "invalid_input"
    else:
        code = "internal_error"
    return {"ok": False, "error": {"code": code, "message": str(exc)}}


@mcp.tool(name="list_devices", description="扫描并列出附近已知的心跳元力 BLE 设备。", structured_output=True)
async def list_devices(prefix: str | None = None, timeout: float = 5.0) -> dict[str, Any]:
    """Return supported devices without connecting or sending commands."""

    manager = DokiDokiDeviceManager()
    try:
        return {"ok": True, **(await manager.list_devices(timeout=timeout, prefix=prefix))}
    except Exception as exc:
        return _error_result(exc)


@mcp.tool(name="connect_device", description="连接指定的心跳元力 BLE 设备并发现 GATT 能力。", structured_output=True)
async def connect_device(ctx: Context, address: str | None = None, name: str | None = None) -> dict[str, Any]:
    try:
        return {"ok": True, **(await _manager(ctx).connect(address=address, name=name))}
    except Exception as exc:
        return _error_result(exc)


@mcp.tool(name="get_device_status", description="读取 MCP 自己持有的设备连接、profile 和 GATT 状态。", structured_output=True)
async def get_device_status(ctx: Context) -> dict[str, Any]:
    try:
        return {"ok": True, **_manager(ctx).status()}
    except Exception as exc:
        return _error_result(exc)


@mcp.tool(name="set_vibration", description="设置 DK-META2 振动强度；非零值必须 confirm=true。", structured_output=True)
async def set_vibration(ctx: Context, level: int, confirm: bool = False) -> dict[str, Any]:
    try:
        return await _manager(ctx).set_action("vibration", level, confirm=confirm)
    except Exception as exc:
        return _error_result(exc)


@mcp.tool(name="set_linear", description="设置 DK-META2 伸缩强度；非零值必须 confirm=true。", structured_output=True)
async def set_linear(ctx: Context, level: int, confirm: bool = False) -> dict[str, Any]:
    try:
        return await _manager(ctx).set_action("linear", level, confirm=confirm)
    except Exception as exc:
        return _error_result(exc)


@mcp.tool(name="set_rotary", description="设置 DK-META2 旋转强度；非零值必须 confirm=true。", structured_output=True)
async def set_rotary(ctx: Context, level: int, confirm: bool = False) -> dict[str, Any]:
    try:
        return await _manager(ctx).set_action("rotary", level, confirm=confirm)
    except Exception as exc:
        return _error_result(exc)


@mcp.tool(name="stop_device", description="将当前设备所有已支持输出归零；可重复调用。", structured_output=True)
async def stop_device(ctx: Context) -> dict[str, Any]:
    try:
        return await _manager(ctx).stop()
    except Exception as exc:
        return _error_result(exc)


@mcp.tool(name="disconnect_device", description="停止心跳并断开 MCP 持有的 BLE 连接。", structured_output=True)
async def disconnect_device(ctx: Context) -> dict[str, Any]:
    try:
        return {"ok": True, **(await _manager(ctx).disconnect(send_stop=True))}
    except Exception as exc:
        return _error_result(exc)


async def _doctor() -> int:
    manager = DokiDokiDeviceManager()
    result: dict[str, Any] = {
        "ok": True,
        "server": "heartbeat-yuanli-mcp",
        "version": "0.1.0",
        "python": sys.version.split()[0],
        "platform": sys.platform,
        "preferred_name": manager.preferred_name,
        "preferred_address_configured": bool(manager.preferred_address),
        "dependencies": {"bleak": True, "mcp": True},
    }
    try:
        result["devices"] = await manager.list_devices(timeout=3.0)
    except Exception as exc:
        result["ok"] = False
        result["error"] = {"code": "doctor_failed", "message": str(exc)}
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["ok"] else 1


def main() -> None:
    logging.basicConfig(level=logging.WARNING, stream=sys.stderr, format="%(levelname)s %(name)s: %(message)s")
    if "--doctor" in sys.argv:
        raise SystemExit(asyncio.run(_doctor()))
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

