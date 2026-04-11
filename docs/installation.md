# Installation

## Requirements

- **Python 3.11 or higher**
- `pip` (bundled with Python 3.4+)
- _(optional)_ FluidSynth or TiMidity for WAV rendering

---

## Install from Source

Clone the repository and install with pip's editable mode:

```bash
git clone https://github.com/ianlintner/audio_engineer.git
cd audio_engineer
pip install -e "."
```

---

## Extras

The package ships several optional dependency groups:

| Extra      | What it adds                                           | Install command                  |
| ---------- | ------------------------------------------------------ | -------------------------------- |
| _(none)_   | Core MIDI generation                                   | `pip install -e "."`             |
| `dev`      | pytest, ruff — required for development                | `pip install -e ".[dev]"`        |
| `api`      | FastAPI + Uvicorn REST server                          | `pip install -e ".[api]"`        |
| `llm`      | LangChain with OpenAI and Anthropic providers          | `pip install -e ".[llm]"`        |
| `gemini`   | Google GenAI SDK — Lyria 3 music generation, audio analysis, TTS | `pip install -e ".[gemini]"` |
| `audio`    | pydub for WAV/MP3 processing                           | `pip install -e ".[audio]"`      |
| `docs`     | MkDocs + Material for building this documentation site | `pip install -e ".[docs]"`       |
| `all`      | Every extra at once                                    | `pip install -e ".[all]"`        |

---

## Audio Rendering (optional)

WAV rendering requires an external audio backend.

=== "FluidSynth"
    ```bash
    # macOS
    brew install fluidsynth

    # Ubuntu / Debian
    sudo apt install fluidsynth

    # Windows (Chocolatey)
    choco install fluidsynth
    ```
    Download a SoundFont (e.g. [GeneralUser GS](https://schristiancollins.com/generaluser.php)) and set `SOUNDFONT_PATH`:
    ```bash
    export SOUNDFONT_PATH=/path/to/soundfont.sf2
    ```

=== "TiMidity"
    ```bash
    # Ubuntu / Debian
    sudo apt install timidity

    # macOS
    brew install timidity
    ```

---

## Verify the Install

```bash
python -c "import audio_engineer; print(audio_engineer.__version__)"
python scripts/generate_demo.py --genre blues --key A --mode minor -v
```

You should see a session ID printed and MIDI files created under `./output/`.
