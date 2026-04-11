#!/usr/bin/env python3
"""Generate a demo backing track using the AI Music Studio."""
import argparse
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from audio_engineer.core.models import (
    Genre, SessionConfig, KeySignature, TimeSignature,
    SectionDef, NoteName, Mode, BandConfig, BandMemberConfig, Instrument,
)
from audio_engineer.agents.orchestrator import SessionOrchestrator


def main():
    parser = argparse.ArgumentParser(description="Generate a demo backing track")
    parser.add_argument(
        "--genre", type=str, default="classic_rock",
        choices=[g.value for g in Genre],
    )
    parser.add_argument("--key", type=str, default="E")
    parser.add_argument("--mode", type=str, default="minor", choices=[m.value for m in Mode])
    parser.add_argument("--tempo", type=int, default=120)
    parser.add_argument("--output", type=str, default="./output")
    parser.add_argument("--render-audio", action="store_true")
    parser.add_argument("--backend", type=str, default="export")
    parser.add_argument("--with-keys", action="store_true", help="Add keyboard to the band")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # Map key string to NoteName
    key_map = {n.value: n for n in NoteName}
    key_root = key_map.get(args.key, NoteName.E)
    mode_map = {m.value: m for m in Mode}
    key_mode = mode_map.get(args.mode, Mode.MINOR)

    # Build band config
    members = [
        BandMemberConfig(instrument=Instrument.DRUMS),
        BandMemberConfig(instrument=Instrument.BASS),
        BandMemberConfig(instrument=Instrument.ELECTRIC_GUITAR),
    ]
    if args.with_keys:
        members.append(BandMemberConfig(instrument=Instrument.KEYS))

    config = SessionConfig(
        genre=Genre(args.genre),
        tempo=args.tempo,
        key=KeySignature(root=key_root, mode=key_mode),
        time_signature=TimeSignature(),
        structure=[
            SectionDef(name="intro", bars=4, intensity=0.5),
            SectionDef(name="verse", bars=8, intensity=0.6),
            SectionDef(name="chorus", bars=8, intensity=0.9),
            SectionDef(name="verse", bars=8, intensity=0.7),
            SectionDef(name="chorus", bars=8, intensity=1.0),
            SectionDef(name="outro", bars=4, intensity=0.4),
        ],
        band=BandConfig(members=members),
    )

    print("\n\U0001f3b8 AI Music Studio - Demo Generator")
    print(f"{'=' * 50}")
    print(f"Genre:  {config.genre.value}")
    print(f"Key:    {config.key.root.value} {config.key.mode.value}")
    print(f"Tempo:  {config.tempo} BPM")
    print(f"Band:   {', '.join(m.instrument.value for m in config.band.members if m.enabled)}")
    total_bars = sum(s.bars * s.repeats for s in config.structure)
    print(f"Length: {total_bars} bars")
    print(f"{'=' * 50}\n")

    orchestrator = SessionOrchestrator(output_dir=args.output)
    session = orchestrator.create_session(config)
    session = orchestrator.run_session(
        session,
        render_audio=args.render_audio,
        backend_name=args.backend,
    )

    print("\n\u2705 Session complete!")
    print(f"Status: {session.status.value}")
    print("Output files:")
    for f in session.output_files:
        print(f"  \U0001f4c4 {f}")
    print()


if __name__ == "__main__":
    main()
