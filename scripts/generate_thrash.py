#!/usr/bin/env python3
"""Generate a thrash metal rhythm section (~2 minutes) to test Gemini integration."""
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from audio_engineer.core.models import (
    Genre, SessionConfig, KeySignature, TimeSignature,
    SectionDef, NoteName, Mode, BandConfig, BandMemberConfig, Instrument,
)
from audio_engineer.agents.orchestrator import SessionOrchestrator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

# Thrash metal: E minor, ~200 BPM, aggressive structure
# At 200 BPM in 4/4, each bar ≈ 1.2s.  ~100 bars ≈ 2 minutes.
config = SessionConfig(
    genre=Genre.HARD_ROCK,          # closest available genre
    tempo=200,                       # thrash tempo
    key=KeySignature(root=NoteName.E, mode=Mode.MINOR),
    time_signature=TimeSignature(numerator=4, denominator=4),
    structure=[
        SectionDef(name="intro",  bars=8,  intensity=0.7),
        SectionDef(name="verse",  bars=16, intensity=0.8),
        SectionDef(name="chorus", bars=8,  intensity=1.0),
        SectionDef(name="verse",  bars=16, intensity=0.85),
        SectionDef(name="chorus", bars=8,  intensity=1.0),
        SectionDef(name="verse",  bars=16, intensity=0.9),
        SectionDef(name="chorus", bars=8,  intensity=1.0),
        SectionDef(name="outro",  bars=16, intensity=0.6),
    ],
    band=BandConfig(members=[
        BandMemberConfig(instrument=Instrument.DRUMS),
        BandMemberConfig(instrument=Instrument.BASS),
        BandMemberConfig(instrument=Instrument.ELECTRIC_GUITAR),
    ]),
)

total_bars = sum(s.bars * s.repeats for s in config.structure)
est_seconds = total_bars * (4 * 60 / config.tempo)

print("\n🤘 Thrash Metal Rhythm Section Generator")
print(f"{'=' * 50}")
print("Key:    E minor")
print(f"Tempo:  {config.tempo} BPM")
print(f"Bars:   {total_bars}")
print(f"Est:    {est_seconds:.0f}s ({est_seconds/60:.1f} min)")
print("Band:   drums, bass, electric guitar")
print(f"{'=' * 50}\n")

# 1. Generate MIDI tracks via the existing orchestrator
orchestrator = SessionOrchestrator(output_dir="./output")
session = orchestrator.create_session(config)
session = orchestrator.run_session(session)

print(f"\n✅ MIDI session {session.id} complete!")
for f in session.output_files:
    print(f"  📄 {f}")

# 2. Test Gemini Lyria integration (if API key is configured)
try:
    from audio_engineer.gemini import MusicGenerationAgent
    from audio_engineer.config.settings import get_settings

    settings = get_settings()
    if settings.gemini_api_key:
        print("\n🎵 Generating Lyria audio rendition...")
        agent = MusicGenerationAgent()
        result = agent.generate_clip(
            "Thrash metal instrumental, E minor, 200 BPM. "
            "Aggressive double-bass drums, fast palm-muted rhythm guitar, "
            "distorted chugging bass. Tight, relentless, high energy. "
            "No vocals.",
            instrumental=True,
        )
        lyria_path = Path(f"./output/{session.id}/{session.id}_lyria_clip.mp3")
        result.save(lyria_path)
        print(f"  🎵 {lyria_path}")
    else:
        print("\n⚠️  AUDIO_ENGINEER_GEMINI_API_KEY not set — skipping Lyria generation")
        print("   Set it in .env or environment to test the Gemini integration")

except ImportError as e:
    print(f"\n⚠️  Gemini SDK not installed — skipping Lyria generation ({e})")
    print("   Install with: pip install 'audio-engineer[gemini]'")

print("\nDone! 🤘")
