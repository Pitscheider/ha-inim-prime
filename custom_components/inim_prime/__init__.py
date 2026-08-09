from datetime import timedelta

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceEntry
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import issue_registry as ir
from inim.prime.native.client import Client as NativeClient
from inim.prime.primelan.client import InimPrimeClient as PrimelanClient
from .adapters.native_adapter import NativeAdapter
from .adapters.primelan_adapter import PrimelanAdapter
from .const import (
    DOMAIN,
    INIM_PRIME_DEVICE_MANUFACTURER,
    ZONES_SCAN_INTERVAL_PRIMELAN_DEFAULT,
    PARTITIONS_SCAN_INTERVAL_PRIMELAN_DEFAULT,
    GSM_SCAN_INTERVAL_PRIMELAN_DEFAULT,
    SYSTEM_FAULTS_SCAN_INTERVAL_PRIMELAN_DEFAULT,
    PANEL_LOG_EVENTS_SCAN_INTERVAL_PRIMELAN_DEFAULT,
    PANEL_LOG_EVENTS_FETCH_LIMIT_DEFAULT,
)
from .coordinators import (
    InimPrimeGSMUpdateCoordinator,
    InimPrimePartitionsUpdateCoordinator,
    InimPrimeZonesUpdateCoordinator,
    InimPrimePanelLogEventsCoordinator,
    InimPrimeSystemFaultsUpdateCoordinator,
)
from .entry_data import (
    get_entry_options,
    get_entry_data,
    InimPrimeConfigData,
    PrimelanConfigData, InimPrimeOptionsData, ScanIntervalsData,
)
from .gateway import InimPrimeGateway
from .runtime_data import (
    InimPrimeConfigEntry,
    InimPrimeCoordinators,
    InimPrimeRuntimeData,
)

PLATFORMS = [
    "binary_sensor",
    "sensor",
    "switch",
    "select",
    "button",
    "event",
]


def _build_gateway(data: InimPrimeConfigData) -> InimPrimeGateway:
    """Construct adapters for whichever backend(s) are configured on this entry.

    Presence of the "native" / "primelan" keys in entry.data is what decides
    whether each backend is active -- there's no separate enable flag.
    """
    native_adapter = None
    primelan_adapter = None

    host = data["host"]
    native_conf = data.get("native")
    primelan_conf = data.get("primelan")

    if native_conf:
        native_client = NativeClient(
            host = host,
            password = native_conf["password"],
            use_outer_frame = native_conf["use_outer_frame"],
            port = native_conf["port"],
            pin = native_conf["pin"],
        )
        native_adapter = NativeAdapter(native_client)


    if primelan_conf:
        primelan_client = PrimelanClient(
            host = host,
            api_key = primelan_conf["api_key"],
            use_https = primelan_conf["use_https"],
        )
        primelan_adapter = PrimelanAdapter(primelan_client)

    return InimPrimeGateway(native = native_adapter, primelan = primelan_adapter)


async def async_setup_entry(hass: HomeAssistant, entry: InimPrimeConfigEntry) -> bool:
    """Set up INIM Prime integration."""
    hass.data.setdefault(DOMAIN, {})

    # Get the data as typed dict
    data = get_entry_data(entry)
    options = get_entry_options(entry)

    # --- Register the panel device ---
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id = entry.entry_id,
        identifiers = {(DOMAIN, data["serial_number"])},
        name = "Inim Prime Panel",
        model = "Prime Panel",
        manufacturer = INIM_PRIME_DEVICE_MANUFACTURER,
        serial_number = data["serial_number"],
    )

    inim_gateway = _build_gateway(data)
    await inim_gateway.connect()

    ###
    ### Coordinators
    ###

    scan_intervals = options["scan_intervals"]

    zones_coordinator: InimPrimeZonesUpdateCoordinator | None = None
    partitions_coordinator: InimPrimePartitionsUpdateCoordinator | None = None
    system_faults_coordinator: InimPrimeSystemFaultsUpdateCoordinator | None = None
    gsm_coordinator: InimPrimeGSMUpdateCoordinator | None = None
    panel_log_events_coordinator: InimPrimePanelLogEventsCoordinator | None = None

    if inim_gateway.supports_zones:
        zones_coordinator = InimPrimeZonesUpdateCoordinator(
            hass = hass,
            update_interval = timedelta(milliseconds = scan_intervals["zones"]),
            entry = entry,
            gateway = inim_gateway,
        )

    if inim_gateway.supports_partitions:
        partitions_coordinator = InimPrimePartitionsUpdateCoordinator(
            hass = hass,
            update_interval = timedelta(milliseconds = scan_intervals["partitions"]),
            entry = entry,
            gateway = inim_gateway,
        )

    if inim_gateway.supports_system_faults:
        system_faults_coordinator = InimPrimeSystemFaultsUpdateCoordinator(
            hass = hass,
            update_interval = timedelta(milliseconds = scan_intervals["system_faults"]),
            entry = entry,
            gateway = inim_gateway,
        )

    if inim_gateway.supports_gsm:
       gsm_coordinator = InimPrimeGSMUpdateCoordinator(
            hass = hass,
            update_interval = timedelta(milliseconds = scan_intervals["gsm"]),
            entry = entry,
            gateway = inim_gateway,
        )

    if inim_gateway.supports_log_events:
        panel_log_events_coordinator = InimPrimePanelLogEventsCoordinator(
            hass = hass,
            update_interval = timedelta(milliseconds = scan_intervals["panel_log_events"]),
            entry = entry,
            gateway = inim_gateway,
        )

    if zones_coordinator is not None:
        await zones_coordinator.async_config_entry_first_refresh()

    if partitions_coordinator is not None:
        await partitions_coordinator.async_config_entry_first_refresh()

    if system_faults_coordinator is not None:
        await system_faults_coordinator.async_config_entry_first_refresh()

    if gsm_coordinator is not None:
        await gsm_coordinator.async_config_entry_first_refresh()

    if panel_log_events_coordinator is not None:
        await panel_log_events_coordinator.async_startup()
        await panel_log_events_coordinator.async_config_entry_first_refresh()

    # Typed, no hass.data[DOMAIN][entry.entry_id] bookkeeping, no manual
    # cleanup of a dict key on unload -- HA clears runtime_data for us.
    entry.runtime_data = InimPrimeRuntimeData(
        gateway = inim_gateway,
        coordinators = InimPrimeCoordinators(
            zones = zones_coordinator,
            partitions = partitions_coordinator,
            gsm = gsm_coordinator,
            system_faults = system_faults_coordinator,
            panel_log_events = panel_log_events_coordinator,
        ),
    )


    await hass.config_entries.async_forward_entry_setups(
        entry = entry,
        platforms = PLATFORMS,
    )

    return True


async def async_remove_config_entry_device(
        hass: HomeAssistant,
        config_entry: InimPrimeConfigEntry,
        device_entry: DeviceEntry,
) -> bool:
    """Allow removing sub-devices but not the panel."""
    for domain, dev_id in device_entry.identifiers:
        # Prevent deleting the panel itself
        data = get_entry_data(config_entry)
        if dev_id == data["serial_number"]:
            return False

    return True


async def async_unload_entry(hass: HomeAssistant, entry: InimPrimeConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        for coordinator in entry.runtime_data.coordinators.all():
            if hasattr(coordinator, "async_shutdown"):
                await coordinator.async_shutdown()
        await entry.runtime_data.gateway.close()

    return unload_ok

async def async_migrate_entry(hass: HomeAssistant, entry: InimPrimeConfigEntry) -> bool:
    """Migrate old (flat, PrimeLAN-only) entries to the native/primelan split schema.

    v1 entries always predate the native backend, so they're unconditionally
    PrimeLAN-only: {serial_number, host, api_key, use_https} becomes
    {serial_number, primelan: {host, api_key, use_https}}.

    Unique IDs and entity unique_ids are keyed off serial_number and
    zone/partition IDs, not the backend, so this migration doesn't touch
    entity registry entries, names, or history.
    """
    if entry.version == 1:
        new_data = InimPrimeConfigData(
            serial_number = entry.data["serial_number"],
            host = entry.data["host"],
            primelan = PrimelanConfigData(
                api_key = entry.data["api_key"],
                use_https = entry.data["use_https"],
            )
        )

        new_options = InimPrimeOptionsData(
            scan_intervals = ScanIntervalsData(
                zones = entry.options["zones_scan_interval"] * 1000 if entry.options.get("zones_scan_interval") is not None else ZONES_SCAN_INTERVAL_PRIMELAN_DEFAULT,
                partitions = entry.options["partitions_scan_interval"] * 1000 if entry.options.get("partitions_scan_interval") is not None else PARTITIONS_SCAN_INTERVAL_PRIMELAN_DEFAULT,
                gsm = entry.options["gsm_scan_interval"] * 1000 if entry.options.get("gsm_scan_interval") is not None else GSM_SCAN_INTERVAL_PRIMELAN_DEFAULT,
                system_faults = entry.options["system_faults_scan_interval"] * 1000 if entry.options.get("system_faults_scan_interval") is not None else SYSTEM_FAULTS_SCAN_INTERVAL_PRIMELAN_DEFAULT,
                panel_log_events = entry.options["panel_log_events_scan_interval"] * 1000 if entry.options.get("panel_log_events_scan_interval") is not None else PANEL_LOG_EVENTS_SCAN_INTERVAL_PRIMELAN_DEFAULT,
            ),
            panel_log_events_fetch_limit = entry.options.get("panel_log_events_fetch_limit", PANEL_LOG_EVENTS_FETCH_LIMIT_DEFAULT),
        )

        @callback
        def update_unique_id(entity_entry: er.RegistryEntry) -> dict | None:
            new_unique_id = None
            # Zones
            if (
                    entity_entry.unique_id.endswith("_exclusion") and
                    "zone" in entity_entry.unique_id
            ):
                new_unique_id = entity_entry.unique_id.removesuffix("_exclusion") + "_bypass"
            # Partitions
            elif (
                    entity_entry.unique_id.endswith("_mode") and
                    "partition" in entity_entry.unique_id
            ):
                new_unique_id = entity_entry.unique_id.removesuffix("_mode") + "_arming_status"
            elif (
                    entity_entry.unique_id.endswith("_clear_alarm_memory") and
                    "partition" in entity_entry.unique_id
            ):
                new_unique_id = entity_entry.unique_id.removesuffix("_clear_alarm_memory") + "_reset_memory"
            # Panel
            elif entity_entry.unique_id.endswith("_excluded_zones_count"):
                new_unique_id = entity_entry.unique_id.removesuffix("_excluded_zones_count") + "_count_bypassed_zones"
            elif entity_entry.unique_id.endswith("_include_all_zones"):
                new_unique_id = entity_entry.unique_id.removesuffix("_include_all_zones") + "_disable_all_zone_bypasses"
            elif entity_entry.unique_id.endswith("_clear_all_partitions_alarm_memory"):
                new_unique_id = entity_entry.unique_id.removesuffix("_clear_all_partitions_alarm_memory") + "_reset_all_partition_memories"
            elif entity_entry.unique_id.endswith("_zones_alarm_memory_count"):
                new_unique_id = entity_entry.unique_id.removesuffix("_zones_alarm_memory_count") + "_count_zone_alarm_memories"
            elif entity_entry.unique_id.endswith("_partitions_alarm_memory_count"):
                new_unique_id = entity_entry.unique_id.removesuffix("_partitions_alarm_memory_count") + "_count_partition_alarm_memories"

            if new_unique_id is not None:
                return {"new_unique_id": new_unique_id}
            else:
                return None

        await er.async_migrate_entries(hass, entry.entry_id, update_unique_id)



        # dentro async_migrate_entry, quando rilevi il cambio enum:
        ir.async_create_issue(
            hass,
            DOMAIN,
            "partition_state_enum_renamed_v2",
            is_fixable = False,
            severity = ir.IssueSeverity.WARNING,
            translation_key = "partition_state_enum_renamed",
        )

        ir.async_create_issue(
            hass,
            DOMAIN,
            "partition_arming_status_enum_renamed_v2",
            is_fixable = False,
            severity = ir.IssueSeverity.WARNING,
            translation_key = "partition_arming_status_enum_renamed",
        )

        ir.async_create_issue(
            hass,
            DOMAIN,
            "zone_state_enum_renamed_v2",
            is_fixable = False,
            severity = ir.IssueSeverity.WARNING,
            translation_key = "zone_state_enum_renamed",
        )

        hass.config_entries.async_update_entry(
            entry,
            data = new_data,
            options = new_options,
            version = 2,
            minor_version = 0,
        )

    return True