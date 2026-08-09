from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceEntry

from .const import (
    DOMAIN,
)
from .custom_types import InimPrimeConfigEntry
from .gateway import InimPrimeGateway


async def async_get_config_entry_diagnostics(
        hass,
        entry: InimPrimeConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for the config entry."""

    gateway = entry.runtime_data.gateway

    diagnostics: dict[str, Any] = {"panel": {
        "serial_number": entry.runtime_data.serial_number,
        "backends_active": gateway.backends_active,
    }, "zones": {
        zone_id: {
            "zone_id": zone.zone_id,
            "terminal": zone.terminal_id,
            "label": zone.label,
            "state": zone.state.name if zone.state is not None else None,
            "bypass": zone.bypass,
            "alarm_memory": zone.alarm_memory,
            "native_status_bytes": zone.native_status_bytes,
            "native_state_str": zone.native_state_str,
        }
        for zone_id, zone in gateway.zones
    }, "partitions": {
        partition_id: {
            "id": partition.partition_id,
            "label": partition.label,
            "partition_state": partition.partition_state.name if partition.partition_state is not None else None,
            "arming_status": partition.arming_status.name if partition.arming_status is not None else None,
            "alarm_memory": partition.alarm_memory,
        }
        for partition_id, partition in gateway.partitions
    }}
    system_faults = gateway.system_faults
    if system_faults is not None:
        diagnostics["system_faults"] = {
            "supply_voltage": system_faults.supply_voltage,
            "faults": [fault.name for fault in system_faults.faults],
        }
    gsm = gateway.gsm
    if gsm is not None:
        diagnostics["gsm"] = {
            "supply_voltage": gsm.supply_voltage,
            "firmware_version": gsm.firmware_version,
            "operator": gsm.operator,
            "signal_strength": gsm.signal_strength,
            "credit": gsm.credit,
        }

    return diagnostics


async def async_get_device_diagnostics(
        hass,
        entry: InimPrimeConfigEntry,
        device: DeviceEntry,
) -> dict[str, Any]:
    """Return diagnostics for a device."""

    gateway: InimPrimeGateway = entry.runtime_data.gateway
    panel_log_events_coordinator = entry.runtime_data.coordinators.panel_log_events

    device_info: dict[str, Any] = {}
    for domain, dev_id in device.identifiers:
        if domain == DOMAIN:
            if "_zone_" in dev_id:
                zone_id = int(dev_id.split("_zone_")[1])
                zone = gateway.get_zone(zone_id)
                if zone:
                    device_info = {
                        "device_type": "zone",
                        "zone_id": zone.zone_id,
                        "terminal": zone.terminal_id,
                        "zone_name": zone.label,
                        "state": zone.state.name if zone.state is not None else None,
                        "bypass": zone.bypass,
                        "alarm_memory": zone.alarm_memory,
                        "native_status_bytes": zone.native_status_bytes,
                        "native_state_str": zone.native_state_str,
                    }

            elif "_partition_" in dev_id:
                partition_id = int(dev_id.split("_partition_")[1])
                partition = gateway.get_partition(partition_id)
                if partition:
                    device_info = {
                        "device_type": "partition",
                        "partition_id": partition.partition_id,
                        "partition_name": partition.label,
                        "partition_state": partition.partition_state.name if partition.partition_state is not None else None,
                        "arming_status": partition.arming_status.name if partition.arming_status is not None else None,
                        "alarm_memory": partition.alarm_memory,
                    }
            elif "_gsm" in dev_id:
                gsm = gateway.gsm
                if gsm is not None:
                    device_info = {
                        "device_type": "gsm",
                        "supply_voltage": gsm.supply_voltage,
                        "firmware_version": gsm.firmware_version,
                        "operator": gsm.operator,
                        "signal_strength": gsm.signal_strength,
                        "credit": gsm.credit,
                    }
                else:
                    device_info = {"device_type": "gsm", "error": "PrimeLAN not configured"}
            else:
                device_info = {
                    "device_type": "panel",
                    "serial_number": entry.runtime_data.serial_number,
                    "backends_active": gateway.backends_active,
                }
                system_faults = gateway.system_faults
                if system_faults is not None:
                    device_info["supply_voltage"] = system_faults.supply_voltage
                    device_info["active_faults"] = [
                        fault.name for fault in system_faults.faults
                    ]
                if panel_log_events_coordinator is not None:
                    device_info["log_events"] = panel_log_events_coordinator.last_panel_log_events

    return device_info
