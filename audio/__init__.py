"""Cadence audio production pipeline.

Modules:
    parser:    Extract AudioJob records from content markdown files
    render:    Translate parsed scripts into ElevenLabs-ready text (with SSML breaks)
    estimate:  Project the cost of generating all audio
    generate:  Call the ElevenLabs API to produce MP3s (requires API key)
    pilot:     Generate a small pilot batch (Variant A week 1) for validation

Run the modules in order:
    1. python -m audio.parser           — verify all content parses cleanly
    2. python -m audio.estimate         — see total characters and projected cost
    3. python -m audio.pilot            — generate the pilot (requires ELEVENLABS_API_KEY)
    4. Listen to the pilot end-to-end before scaling.
    5. python -m audio.generate         — full production run after pilot validates
"""
