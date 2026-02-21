# Migration to Free APIs

## What Changed

- **LLM**: OpenAI GPT-4 -> Groq Llama 3.1 70B (FREE) with OpenAI fallback
- **TTS**: OpenAI TTS -> gTTS (FREE) with OpenAI fallback
- **Architecture**: Direct API calls -> Provider abstraction with factory pattern

## Backward Compatibility

- All existing code works without changes
- All 374 original tests still pass
- Can still use OpenAI if preferred
- Automatic fallback between providers

## New Architecture

```
neurosync/
  llm/
    base_provider.py      # Abstract LLM interface
    groq_provider.py      # Groq implementation (FREE)
    openai_provider.py    # OpenAI implementation
    factory.py            # Provider factory with fallback
  tts/
    base_provider.py      # Abstract TTS interface
    gtts_provider.py      # gTTS implementation (FREE)
    factory.py            # TTS factory
```

## How Provider Selection Works

1. `LLM_PROVIDER` env var selects primary provider ("groq" or "openai")
2. If primary is unavailable, factory falls back to alternative
3. InterventionGenerator and ContentPipeline auto-detect provider from env
4. Tests inject mock clients directly (unchanged)

## Setup

1. Get Groq API key (FREE): https://console.groq.com/keys
2. Add to `.env`: `GROQ_API_KEY=gsk_xxx`
3. Set provider: `LLM_PROVIDER=groq`
4. Done. System uses FREE APIs.

## Testing

```bash
# Test providers work
pytest tests/test_llm_providers.py -v
pytest tests/test_tts_providers.py -v

# Test integration
pytest tests/test_migration_integration.py -v

# Test full system (should be 425+ passing)
pytest tests/ -v
```

## Rollback

To revert to OpenAI only:
```bash
LLM_PROVIDER=openai
TTS_PROVIDER=openai
OPENAI_API_KEY=sk-proj-xxx
```

No code changes needed.
