from abc import ABC, abstractmethod


class ProviderError(Exception):
    """Friendly, user-safe error raised by any storage adapter."""


class ProviderUnavailable(ProviderError):
    pass


class ObjectNotFound(ProviderError):
    pass


class StorageProvider(ABC):
    name: str = "provider"
    label: str = "Provider"

    @abstractmethod
    def upload(self, key: str, data: bytes, content_type: str) -> None: ...

    @abstractmethod
    def download(self, key: str) -> bytes: ...

    @abstractmethod
    def delete(self, key: str) -> None: ...

    @abstractmethod
    def exists(self, key: str) -> bool: ...

    @abstractmethod
    def get_metadata(self, key: str) -> dict: ...

    @abstractmethod
    def health(self) -> bool: ...


class GuardedProvider(StorageProvider):
    """Wraps a provider; when simulate_down is set every operation fails (software-level simulation only)."""

    def __init__(self, inner: StorageProvider, simulate_down: bool = False):
        self.inner, self.simulate_down = inner, bool(simulate_down)
        self.name, self.label = inner.name, inner.label

    def _check(self):
        if self.simulate_down:
            raise ProviderUnavailable(f"{self.label} is unavailable (simulated failure).")

    def upload(self, key, data, content_type):
        self._check()
        return self.inner.upload(key, data, content_type)

    def download(self, key):
        self._check()
        return self.inner.download(key)

    def delete(self, key):
        self._check()
        return self.inner.delete(key)

    def exists(self, key):
        self._check()
        return self.inner.exists(key)

    def get_metadata(self, key):
        self._check()
        return self.inner.get_metadata(key)

    def health(self):
        return False if self.simulate_down else self.inner.health()
