"""Shared provider errors."""


class MissingCredentialError(RuntimeError):
    """Raised when a live provider is selected without a credential.

    Callers must not replace this with a fabricated successful response.
    """


class ProviderNotConfiguredError(RuntimeError):
    """Raised when a named provider has no real adapter yet."""
