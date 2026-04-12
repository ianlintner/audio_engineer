"""Tests for LLMMidiProvider: prompt building, JSON parsing, fallback behaviour."""
import json
from audio_engineer.core.llm_prompts import (
    build_midi_prompt,
    parse_midi_json,
    validate_midi_events,
    events_to_note_events,
)
from audio_engineer.providers.base import TrackRequest, ProviderCapability
from audio_engineer.providers.llm_midi_provider import LLMMidiProvider


# ---------------------------------------------------------------------------
# llm_prompts helpers
# ---------------------------------------------------------------------------

class TestBuildMidiPrompt:
    def test_contains_instrument(self):
        req = TrackRequest(track_name="test", description="", instrument="bass", genre="funk")
        prompt = build_midi_prompt(req)
        assert "bass" in prompt

    def test_contains_genre(self):
        req = TrackRequest(track_name="test", description="", genre="jazz")
        prompt = build_midi_prompt(req)
        assert "jazz" in prompt

    def test_contains_tempo(self):
        req = TrackRequest(track_name="test", description="", tempo=140)
        prompt = build_midi_prompt(req)
        assert "140" in prompt

    def test_json_schema_included(self):
        req = TrackRequest(track_name="test", description="")
        prompt = build_midi_prompt(req)
        assert "pitch" in prompt
        assert "velocity" in prompt
        assert "start_beat" in prompt
        assert "duration_beats" in prompt


class TestParseMidiJson:
    def test_plain_json_array(self):
        text = '[{"pitch": 60, "velocity": 80, "start_beat": 1.0, "duration_beats": 1.0}]'
        result = parse_midi_json(text)
        assert result is not None
        assert len(result) == 1
        assert result[0]["pitch"] == 60

    def test_strips_markdown_fences(self):
        text = "```json\n[{\"pitch\": 60, \"velocity\": 80, \"start_beat\": 1.0, \"duration_beats\": 1.0}]\n```"
        result = parse_midi_json(text)
        assert result is not None
        assert result[0]["pitch"] == 60

    def test_strips_plain_fences(self):
        text = "```\n[{\"pitch\": 60, \"velocity\": 80, \"start_beat\": 1.0, \"duration_beats\": 1.0}]\n```"
        result = parse_midi_json(text)
        assert result is not None

    def test_returns_none_on_bad_json(self):
        assert parse_midi_json("not json at all") is None

    def test_returns_none_on_empty(self):
        assert parse_midi_json("") is None

    def test_returns_none_when_no_array(self):
        assert parse_midi_json('{"pitch": 60}') is None

    def test_multiple_notes(self):
        notes = [
            {"pitch": 60, "velocity": 80, "start_beat": 1.0, "duration_beats": 1.0},
            {"pitch": 64, "velocity": 75, "start_beat": 2.0, "duration_beats": 0.5},
        ]
        text = json.dumps(notes)
        result = parse_midi_json(text)
        assert len(result) == 2


class TestValidateMidiEvents:
    def _note(self, pitch=60, velocity=80, start=1.0, dur=1.0):
        return {"pitch": pitch, "velocity": velocity, "start_beat": start, "duration_beats": dur}

    def test_valid_event_passes(self):
        events = [self._note()]
        result = validate_midi_events(events)
        assert len(result) == 1

    def test_out_of_range_pitch_clamped(self):
        events = [self._note(pitch=200)]
        result = validate_midi_events(events)
        assert len(result) == 1
        assert result[0]["pitch"] == 127

    def test_negative_pitch_clamped(self):
        events = [self._note(pitch=-1)]
        result = validate_midi_events(events)
        assert len(result) == 1
        assert result[0]["pitch"] == 0

    def test_zero_velocity_clamped(self):
        events = [self._note(velocity=0)]
        result = validate_midi_events(events)
        assert len(result) == 1
        assert result[0]["velocity"] == 1

    def test_start_beat_before_1_rejected(self):
        events = [self._note(start=0.5)]
        assert validate_midi_events(events) == []

    def test_start_beat_after_bar_rejected(self):
        events = [self._note(start=5.5)]
        assert validate_midi_events(events, beats_per_bar=4) == []

    def test_zero_duration_rejected(self):
        events = [self._note(dur=0.0)]
        assert validate_midi_events(events) == []

    def test_non_dict_items_skipped(self):
        events = ["not_a_dict", self._note()]
        result = validate_midi_events(events)
        assert len(result) == 1

    def test_max_notes_limit(self):
        events = [self._note() for _ in range(200)]
        result = validate_midi_events(events, max_notes=50)
        assert len(result) == 50


class TestEventsToNoteEvents:
    def test_converts_correctly(self):
        events = [{"pitch": 60, "velocity": 80, "start_beat": 1.0, "duration_beats": 1.0}]
        note_events = events_to_note_events(events, channel=0, ticks_per_beat=480)
        assert len(note_events) == 1
        ne = note_events[0]
        assert ne.pitch == 60
        assert ne.velocity == 80
        assert ne.start_tick == 0  # beat 1 = tick 0
        assert ne.duration_ticks == 480
        assert ne.channel == 0

    def test_bar_offset_applied(self):
        events = [{"pitch": 60, "velocity": 80, "start_beat": 1.0, "duration_beats": 1.0}]
        ne = events_to_note_events(events, ticks_per_beat=480, bar_offset_ticks=1920)
        assert ne[0].start_tick == 1920


# ---------------------------------------------------------------------------
# LLMMidiProvider
# ---------------------------------------------------------------------------

class TestLLMMidiProvider:
    def test_unavailable_without_llm(self):
        provider = LLMMidiProvider(llm=None)
        assert not provider.is_available()

    def test_available_with_llm(self):
        provider = LLMMidiProvider(llm=lambda p: "[]")
        assert provider.is_available()

    def test_capability_is_midi_generation(self):
        provider = LLMMidiProvider()
        assert ProviderCapability.MIDI_GENERATION in provider.capabilities

    def test_name(self):
        assert LLMMidiProvider().name == "llm_midi"

    def test_no_llm_returns_failure(self):
        provider = LLMMidiProvider(llm=None)
        req = TrackRequest(track_name="t", description="", instrument="keys")
        result = provider.generate_track(req)
        assert not result.success
        assert result.error is not None

    def test_valid_llm_response_generates_track(self):
        notes = [
            {"pitch": 60, "velocity": 80, "start_beat": 1.0, "duration_beats": 1.0},
            {"pitch": 64, "velocity": 75, "start_beat": 2.0, "duration_beats": 1.0},
            {"pitch": 67, "velocity": 72, "start_beat": 3.0, "duration_beats": 1.0},
            {"pitch": 64, "velocity": 70, "start_beat": 4.0, "duration_beats": 1.0},
        ]

        def mock_llm(prompt):
            return json.dumps(notes)

        provider = LLMMidiProvider(llm=mock_llm)
        req = TrackRequest(track_name="test_keys", description="", instrument="keys", genre="jazz", tempo=120)
        result = provider.generate_track(req)
        assert result.success
        assert result.track is not None
        assert result.track.midi_data is not None
        assert len(result.track.midi_data.events) > 0

    def test_bad_llm_response_falls_back_to_midi_provider(self):
        def bad_llm(prompt):
            return "this is not JSON"

        provider = LLMMidiProvider(llm=bad_llm)
        req = TrackRequest(track_name="test", description="", instrument="keys", genre="pop")
        result = provider.generate_track(req)
        # Fallback to MidiProvider succeeds
        assert result.success
        assert "fallback" in result.provider_used

    def test_llm_exception_falls_back(self):
        def crashing_llm(prompt):
            raise RuntimeError("API down")

        provider = LLMMidiProvider(llm=crashing_llm)
        req = TrackRequest(track_name="test", description="", instrument="bass")
        result = provider.generate_track(req)
        assert result.success  # fallback succeeds
        assert "fallback" in result.provider_used

    def test_tracks_named_correctly(self):
        notes = [{"pitch": 60, "velocity": 80, "start_beat": 1.0, "duration_beats": 1.0}]

        def mock_llm(p):
            return json.dumps(notes)

        provider = LLMMidiProvider(llm=mock_llm)
        req = TrackRequest(track_name="my_track", description="", instrument="keys")
        result = provider.generate_track(req)
        assert result.track.name == "my_track"
