"""Exceptions raised by the INIM Prime integration's gateway layer."""


class InimPrimeFeatureNotSupportedError(Exception):
    """Raised when a feature is requested but no configured backend supports it.

    Typically means the integration is running native-only and something
    that currently requires PrimeLAN (GSM, system faults, log events,
    scenarios, output dimming) was requested.
    """
