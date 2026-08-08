from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from inim.prime.native.client import Client as NativeClient
from inim.prime.primelan.client import InimPrimeClient as PrimelanClient

from .adapters.native_adapter import NativeAdapter
from .adapters.primelan_adapter import PrimelanAdapter

from .gateway import InimPrimeGateway
from .const import (
    CONF_SERIAL_NUMBER,
    DOMAIN,
    INIM_PRIME_DEVICE_MANUFACTURER,

    # --- Coordinators ---
    PANEL_LOG_EVENTS_COORDINATOR,
    ZONES_COORDINATOR,
    PARTITIONS_COORDINATOR,
    GSM_COORDINATOR,
    SYSTEM_FAULTS_COORDINATOR,

    # --- Scan interval config keys ---
    CONF_ZONES_SCAN_INTERVAL,
    CONF_PARTITIONS_SCAN_INTERVAL,
    CONF_GSM_SCAN_INTERVAL,
    CONF_SYSTEM_FAULTS_SCAN_INTERVAL,
    CONF_PANEL_LOG_EVENTS_SCAN_INTERVAL,

    # --- Defaults (custom per coordinator) ---
    CONF_ZONES_SCAN_INTERVAL_PRIMELAN_DEFAULT,
    CONF_PARTITIONS_SCAN_INTERVAL_PRIMELAN_DEFAULT,
    CONF_GSM_SCAN_INTERVAL_PRIMELAN_DEFAULT,
    CONF_SYSTEM_FAULTS_SCAN_INTERVAL_PRIMELAN_DEFAULT,
    CONF_PANEL_LOG_EVENTS_SCAN_INTERVAL_PRIMELAN_DEFAULT, CONF_HOST, CONF_PRIMELAN_API_KEY, CONF_PRIMELAN_USE_HTTPS, CONF_NATIVE,
    CONF_PRIMELAN, CONF_NATIVE_PASSWORD, CONF_NATIVE_USE_OUTER_FRAME, CONF_NATIVE_PORT, CONF_NATIVE_PIN,
)
from .coordinators import (
    InimPrimeGSMUpdateCoordinator,
    InimPrimePartitionsUpdateCoordinator,
    InimPrimeZonesUpdateCoordinator,
    InimPrimePanelLogEventsCoordinator,
    InimPrimeSystemFaultsUpdateCoordinator,
)

PLATFORMS = [
    "binary_sensor",
    "sensor",
    "switch",
    "select",
    "button",
    "event",
]

def _build_gateway(entry: ConfigEntry) -> InimPrimeGateway:
    """Construct adapters for whichever backend(s) are configured on this entry.

    Presence of the "native" / "primelan" keys in entry.data is what decides
    whether each backend is active -- there's no separate enable flag.
    """
    native_adapter = None
    primelan_adapter = None

    host: str = entry.data[CONF_HOST]
    native_conf = entry.data.get(CONF_NATIVE)
    primelan_conf = entry.data.get(CONF_PRIMELAN)

    if native_conf:
        native_client = NativeClient(
            host = host,
            password = native_conf[CONF_NATIVE_PASSWORD],
            use_outer_frame = native_conf[CONF_NATIVE_USE_OUTER_FRAME],
            port = native_conf[CONF_NATIVE_PORT],
            pin = native_conf[CONF_NATIVE_PIN],
        )
        native_adapter = NativeAdapter(native_client)


    if primelan_conf:
        primelan_client = PrimelanClient(
            host = host,
            api_key = primelan_conf[CONF_PRIMELAN_API_KEY],
            use_https = primelan_conf.get(CONF_PRIMELAN_USE_HTTPS, True),
        )
        primelan_adapter = PrimelanAdapter(primelan_client)

    return InimPrimeGateway(native = native_adapter, primelan = primelan_adapter)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up INIM Prime integration."""
    hass.data.setdefault(DOMAIN, {})

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))


    # --- Register the panel device ---
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id = entry.entry_id,
        identifiers = {(DOMAIN, entry.data[CONF_SERIAL_NUMBER])},
        name = "Inim Prime Panel",
        model = "Prime Panel",
        manufacturer = INIM_PRIME_DEVICE_MANUFACTURER,
        serial_number = entry.data[CONF_SERIAL_NUMBER],
    )

    gateway = _build_gateway(entry)
    await gateway.connect()

    ###
    ### Coordinators
    ###

    scan_intervals = entry.options.get("scan_intervals", {})

    zones_scan_interval = scan_intervals.get(
        CONF_ZONES_SCAN_INTERVAL,
        CONF_ZONES_SCAN_INTERVAL_PRIMELAN_DEFAULT,
    )
    partitions_scan_interval = scan_intervals.get(
        CONF_PARTITIONS_SCAN_INTERVAL,
        CONF_PARTITIONS_SCAN_INTERVAL_PRIMELAN_DEFAULT,
    )
    gsm_scan_interval = scan_intervals.get(
        CONF_GSM_SCAN_INTERVAL,
        CONF_GSM_SCAN_INTERVAL_PRIMELAN_DEFAULT,
    )
    system_faults_scan_interval = scan_intervals.get(
        CONF_SYSTEM_FAULTS_SCAN_INTERVAL,
        CONF_SYSTEM_FAULTS_SCAN_INTERVAL_PRIMELAN_DEFAULT,
    )
    panel_log_events_scan_interval = scan_intervals.get(
        CONF_PANEL_LOG_EVENTS_SCAN_INTERVAL,
        CONF_PANEL_LOG_EVENTS_SCAN_INTERVAL_PRIMELAN_DEFAULT,
    )

    inim_prime_coordinators: dict[str, DataUpdateCoordinator]

    # Zones & partitions are always available (both backends support them).
    inim_prime_coordinators = {
        ZONES_COORDINATOR: InimPrimeZonesUpdateCoordinator(
            hass = hass,
            update_interval = timedelta(milliseconds = zones_scan_interval),
            entry = entry,
            gateway = gateway,
        ),
        PARTITIONS_COORDINATOR: InimPrimePartitionsUpdateCoordinator(
            hass = hass,
            update_interval = timedelta(milliseconds = partitions_scan_interval),
            entry = entry,
            gateway = gateway,
        ),
    }

    # GSM / system faults / log events are PrimeLAN-only today. On a
    # native-only entry, these coordinators simply don't exist, and the
    # corresponding platforms create zero entities for them (see their
    # updated async_setup_entry, which does coordinators.get(...) and
    # returns/skips when None).
    if gateway.supports_system_faults:
        inim_prime_coordinators[SYSTEM_FAULTS_COORDINATOR] = InimPrimeSystemFaultsUpdateCoordinator(
            hass = hass,
            update_interval = timedelta(milliseconds = system_faults_scan_interval),
            entry = entry,
            gateway = gateway,
        )

    if gateway.supports_gsm:
        inim_prime_coordinators[GSM_COORDINATOR] = InimPrimeGSMUpdateCoordinator(
            hass = hass,
            update_interval = timedelta(milliseconds = gsm_scan_interval),
            entry = entry,
            gateway = gateway,
        )

    if gateway.supports_log_events:
        inim_prime_coordinators[PANEL_LOG_EVENTS_COORDINATOR] = InimPrimePanelLogEventsCoordinator(
            hass = hass,
            update_interval = timedelta(milliseconds = panel_log_events_scan_interval),
            entry = entry,
            gateway = gateway,
        )

    await inim_prime_coordinators[ZONES_COORDINATOR].async_config_entry_first_refresh()
    await inim_prime_coordinators[PARTITIONS_COORDINATOR].async_config_entry_first_refresh()

    if SYSTEM_FAULTS_COORDINATOR in inim_prime_coordinators:
        await inim_prime_coordinators[SYSTEM_FAULTS_COORDINATOR].async_config_entry_first_refresh()

    if GSM_COORDINATOR in inim_prime_coordinators:
        await inim_prime_coordinators[GSM_COORDINATOR].async_config_entry_first_refresh()

    if PANEL_LOG_EVENTS_COORDINATOR in inim_prime_coordinators:
        await inim_prime_coordinators[PANEL_LOG_EVENTS_COORDINATOR].async_startup()
        await inim_prime_coordinators[PANEL_LOG_EVENTS_COORDINATOR].async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "gateway": gateway,
        "coordinators": inim_prime_coordinators,
    }

    await hass.config_entries.async_forward_entry_setups(
        entry = entry,
        platforms = PLATFORMS,
    )

    return True


async def async_remove_config_entry_device(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        device_entry: DeviceEntry,
) -> bool:
    """Allow removing sub-devices but not the panel."""
    for domain, dev_id in device_entry.identifiers:
        # Prevent deleting the panel itself
        if dev_id == config_entry.data[CONF_SERIAL_NUMBER]:
            return False

    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload INIM Prime config entry."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload INIM Prime integration."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry = entry,
        platforms = PLATFORMS,
    )

    if unload_ok:
        data = hass.data[DOMAIN].pop(entry.entry_id)

        # Stop coordinators (optional but recommended)
        inim_prime_coordinators = data.get("coordinators", {})

        for coordinator in inim_prime_coordinators.values():
            if coordinator and hasattr(coordinator, "async_shutdown"):
                await coordinator.async_shutdown()

        # Close API gateway
        await data["gateway"].close()

    return unload_ok

async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate old (flat, PrimeLAN-only) entries to the native/primelan split schema.

    v1 entries always predate the native backend, so they're unconditionally
    PrimeLAN-only: {serial_number, host, api_key, use_https} becomes
    {serial_number, primelan: {host, api_key, use_https}}.

    Unique IDs and entity unique_ids are keyed off serial_number and
    zone/partition IDs, not the backend, so this migration doesn't touch
    entity registry entries, names, or history.
    """
    if entry.version == 1:
        new_data = {**entry.data}

        new_data[CONF_PRIMELAN] = {
            CONF_HOST: new_data.pop(CONF_HOST),
            CONF_PRIMELAN_API_KEY: new_data.pop(CONF_PRIMELAN_API_KEY),
            CONF_PRIMELAN_USE_HTTPS: new_data.pop(CONF_PRIMELAN_USE_HTTPS, True),
        }

        hass.config_entries.async_update_entry(
            entry,
            data = new_data,
            version = 2,
            minor_version = 0,
        )

    return True