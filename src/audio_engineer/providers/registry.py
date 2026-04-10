"""Provider registry with capability-based routing."""
from __future__ import annotations

import logging
from typing import Optional

from audio_engineer.providers.base import (
    AudioProvider,
    ProviderCapability,
    TrackRequest,
    TrackResult,
)

logger = logging.getLogger(__name__)


class ProviderRegistry:
    """Manages registered audio providers and routes requests to them.

    Routing priority:
    1. If ``preferred_provider`` is set and available, use it.
    2. If ``required_capabilities`` are set, find the first available
       provider that supports all of them.
    3. Fall back to the first available provider.
    """

    def __init__(self) -> None:
        self._providers: dict[str, AudioProvider] = {}

    def register(self, provider: AudioProvider) -> None:
        """Register a provider. Overwrites existing with same name."""
        self._providers[provider.name] = provider
        logger.info("Registered provider: %s (capabilities: %s)",
                     provider.name, [c.value for c in provider.capabilities])

    def get(self, name: str) -> Optional[AudioProvider]:
        """Get a provider by name, or None."""
        return self._providers.get(name)

    def list_providers(self) -> list[str]:
        """All registered provider names."""
        return list(self._providers.keys())

    def list_available(self) -> list[str]:
        """Names of providers that are currently available."""
        return [name for name, p in self._providers.items() if p.is_available()]

    def find_by_capability(
        self, capability: ProviderCapability
    ) -> list[AudioProvider]:
        """Return available providers that support the given capability."""
        return [
            p for p in self._providers.values()
            if p.is_available() and p.supports(capability)
        ]

    def route(self, request: TrackRequest) -> Optional[AudioProvider]:
        """Select the best provider for a request.

        Returns None if no suitable provider is found.
        """
        # 1. Preferred provider override
        if request.preferred_provider:
            preferred = self.get(request.preferred_provider)
            if preferred and preferred.is_available():
                return preferred
            logger.debug(
                "Preferred provider '%s' unavailable, falling back",
                request.preferred_provider,
            )

        # 2. Match by required capabilities
        if request.required_capabilities:
            for provider in self._providers.values():
                if not provider.is_available():
                    continue
                if all(provider.supports(c) for c in request.required_capabilities):
                    return provider
            return None

        # 3. Default: first available provider
        for provider in self._providers.values():
            if provider.is_available():
                return provider

        return None

    def generate(self, request: TrackRequest) -> TrackResult:
        """Route the request and generate the track."""
        provider = self.route(request)
        if provider is None:
            return TrackResult(
                track=None,
                success=False,
                provider_used="none",
                error=f"No provider found for request '{request.track_name}' "
                      f"with capabilities {[c.value for c in request.required_capabilities]}",
            )

        logger.info("Routing '%s' to provider '%s'", request.track_name, provider.name)
        return provider.generate_track(request)
