# Skill: midi-style-refiner

## Purpose
Refine generated MIDI patterns so they remain genre-appropriate while preserving harmonic correctness and groove consistency.

## Use when
- A generated part feels stylistically off.
- Dynamics or articulations need genre shaping.
- You need to preserve deterministic output while improving feel.

## Inputs
- Genre and style hints.
- Existing section/chord progression.
- Candidate MIDI note events.

## Output expectations
- Keep note timing within configured quantization/humanization bounds.
- Do not violate chord tones unless intentional passing tones are requested.
- Explain changes briefly and include why they improve style fit.
