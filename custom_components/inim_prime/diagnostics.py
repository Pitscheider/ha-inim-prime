from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntry

from .const import (
    DOMAIN,
    CONF_SERIAL_NUMBER,
    PANEL_LOG_EVENTS_COORDINATOR,
    ZONES_COORDINATOR,
    PARTITIONS_COORDINATOR,
    SYSTEM_FAULTS_COORDINATOR,
    GSM_COORDINATOR,
)

from .coordinators import (
    InimPrimeZonesUpdateCoordinator,
    InimPrimePartitionsUpdateCoordinator,
    InimPrimeSystemFaultsUpdateCoordinator,
    InimPrimeGSMUpdateCoordinator,
    InimPrimePanelLogEventsCoordinator,
)
from .gateway import InimPrimeGateway


async def async_get_config_entry_diagnostics(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for the config entry."""
    entry_data = hass.data[DOMAIN][config_entry.entry_id]
    coordinators = entry_data["coordinators"]
    gateway: InimPrimeGateway = entry_data["gateway"]

    zones_coordinator: InimPrimeZonesUpdateCoordinator = coordinators[ZONES_COORDINATOR]
    partitions_coordinator: InimPrimePartitionsUpdateCoordinator = coordinators[PARTITIONS_COORDINATOR]
    system_faults_coordinator: InimPrimeSystemFaultsUpdateCoordinator | None = coordinators.get(
        SYSTEM_FAULTS_COORDINATOR
    )
    gsm_coordinator: InimPrimeGSMUpdateCoordinator | None = coordinators.get(GSM_COORDINATOR)

    diagnostics: dict[str, Any] = {
        "panel": {
            "serial_number": config_entry.data[CONF_SERIAL_NUMBER],
            "backends_active": gateway.backends_active,
        },
        "zones": {
            zone_id: {
                "zone_id": zone.zone_id,
                "terminal": zone.terminal_id,
                "label": zone.label,
                "state": zone.state.name if zone.state is not None else None,
                "bypass": zone.bypass,
                "alarm_memory": zone.alarm_memory,
                "native_status_bytes": zone.native_status_bytes,
            }
            for zone_id, zone in zones_coordinator.data.items()
        },
        "partitions": {
            partition_id: {
                "id": partition.partition_id,
                "label": partition.label,
                "partition_state": partition.partition_state.name if partition.partition_state is not None else None,
                "arming_status": partition.arming_status.name if partition.arming_status is not None else None,
                "alarm_memory": partition.alarm_memory,
            }
            for partition_id, partition in partitions_coordinator.data.items()
        },
    }

    if system_faults_coordinator is not None:
        diagnostics["system_faults"] = {
            "supply_voltage": system_faults_coordinator.data.supply_voltage,
            "faults": [fault.name for fault in system_faults_coordinator.data.faults],
        }

    if gsm_coordinator is not None:
        diagnostics["gsm"] = {
            "supply_voltage": gsm_coordinator.data.supply_voltage,
            "firmware_version": gsm_coordinator.data.firmware_version,
            "operator": gsm_coordinator.data.operator,
            "signal_strength": gsm_coordinator.data.signal_strength,
            "credit": gsm_coordinator.data.credit,
        }

    return diagnostics


async def async_get_device_diagnostics(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        device: DeviceEntry,
) -> dict[str, Any]:
    """Return diagnostics for a device."""

    entry_data = hass.data[DOMAIN][config_entry.entry_id]
    coordinators = entry_data["coordinators"]
    gateway: InimPrimeGateway = entry_data["gateway"]

    zones_coordinator: InimPrimeZonesUpdateCoordinator = coordinators[ZONES_COORDINATOR]
    partitions_coordinator: InimPrimePartitionsUpdateCoordinator = coordinators[PARTITIONS_COORDINATOR]
    system_faults_coordinator: InimPrimeSystemFaultsUpdateCoordinator | None = coordinators.get(
        SYSTEM_FAULTS_COORDINATOR
    )
    gsm_coordinator: InimPrimeGSMUpdateCoordinator | None = coordinators.get(GSM_COORDINATOR)
    panel_log_events_coordinator: InimPrimePanelLogEventsCoordinator | None = coordinators.get(
        PANEL_LOG_EVENTS_COORDINATOR
    )

    device_info: dict[str, Any] = {}
    for domain, dev_id in device.identifiers:
        if domain == DOMAIN:
            if "_zone_" in dev_id:
                zone_id = int(dev_id.split("_zone_")[1])
                zone = zones_coordinator.data.get(zone_id)
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
                    }

            elif "_partition_" in dev_id:
                partition_id = int(dev_id.split("_partition_")[1])
                partition = partitions_coordinator.data.get(partition_id)
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
                if gsm_coordinator is not None:
                    gsm = gsm_coordinator.data
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
                    "serial_number": config_entry.data[CONF_SERIAL_NUMBER],
                    "backends_active": gateway.backends_active,
                }
                if system_faults_coordinator is not None:
                    device_info["supply_voltage"] = system_faults_coordinator.data.supply_voltage
                    device_info["active_faults"] = [
                        fault.name for fault in system_faults_coordinator.data.faults
                    ]
                if panel_log_events_coordinator is not None:
                    device_info["log_events"] = panel_log_events_coordinator.last_panel_log_events

    return device_info
