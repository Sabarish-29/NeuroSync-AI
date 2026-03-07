"""NeuroSync AI — TTS provider abstraction layer."""

from neurosync.tts.base_provider import BaseTTSProvider, TTSResult
from neurosync.tts.factory import TTSProviderFactory
from neurosync.tts.gtts_provider import GTTSProvider

__all__ = [
    "BaseTTSProvider",
    "TTSResult",
    "TTSProviderFactory",
    "GTTSProvider",
]
