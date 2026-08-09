from __future__ import annotations

from inim.prime.native.client import Client as NativeClient
from inim.prime.primelan.client import InimPrimeClient

from .models import NativeConfig, PrimelanConfig


async def test_native_connection(native_conf: NativeConfig, host: str) -> None:
    client = NativeClient(
        host = host, password = native_conf.password,
        use_outer_frame = native_conf.use_outer_frame,
        port = native_conf.port, pin = native_conf.pin,
    )
    await client.connect()
    await client.initialize()
    client.disconnect()


async def test_native_connection_and_get_serial(native_conf: NativeConfig, host: str) -> str:
    client = NativeClient(
        host = host, password = native_conf.password,
        use_outer_frame = native_conf.use_outer_frame,
        port = native_conf.port, pin = native_conf.pin,
    )
    await client.connect()
    await client.initialize()
    try:
        panel_info = client.panel_info
        serial_number = panel_info[0] if panel_info else None
    finally:
        client.disconnect()

    if not serial_number:
        raise ValueError("Native panel did not report a serial number")
    return serial_number


async def test_primelan_connection(primelan_conf: PrimelanConfig, host: str) -> None:
    client = InimPrimeClient(host = host, api_key = primelan_conf.api_key, use_https = primelan_conf.use_https)
    await client.connect()
    await client.close()