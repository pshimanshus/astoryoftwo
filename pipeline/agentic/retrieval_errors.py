class BackendUnavailable(RuntimeError):
    """An optional backend was not enabled or its dependency is absent."""


class BackendStale(RuntimeError):
    """A derived backend index is missing or does not match the manifest."""
