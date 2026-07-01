# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Football Symphony transforms football (soccer) match data into musical compositions. Each player is mapped to a random musical note, and match events (passes, shots, fouls, goals) produce drum/percussion sounds. Data comes from StatsBomb's free event data, and music is generated using the music21 library with FluidSynth for MIDI-to-WAV synthesis.

## Commands

```bash
# Run the app locally (Dash dev server on port 8000)
python app.py

# Update cached data from StatsBomb API (toggle save_* flags inside the script)
python data_preprocessing.py

# Production (Docker)
docker build -t football-symphony .
docker run -p 80:80 football-symphony

# Production (Heroku)
# Uses Procfile: gunicorn app:server
```

System dependency required for audio: `fluidsynth` (installed via apt in Docker, needs `brew install fluid-synth` on macOS).

## Architecture

Four Python modules, no test suite:

- **app.py** — Dash web application. Defines UI layout (Bootstrap grid with cascading dropdowns: Competition → Season → Match), Dash callbacks for user interactions, and client-side state via `dcc.Store` components (`store-events`, `store-players`, `store-notes`, `store-timestr`).
- **common.py** — Loaded at import time. Deserializes all pickle/parquet lookup tables from `assets/data/` into module-level constants (COMP_ITN, SZN_ITN, COMP_TO_SZNS, SZN_TO_MATCHES, MATCHES_ITN, NAME_TO_NICKNAME) and defines instrument lists.
- **utils.py** — Core music generation. `make_stream()` builds a music21 Score with three parts (mainPart for melody, drumPart for event percussion, goalPart for goal fanfares). `generate_music21()` orchestrates stream creation and FluidSynth WAV conversion. Also contains `sample_notes()` for random player-to-note assignment.
- **data_preprocessing.py** — Offline data pipeline. Fetches from StatsBomb API via `statsbombpy`, saves competitions/matches as Parquet and lookup dicts as pickle files. Each step is gated by a `save_*` boolean flag that must be manually toggled to `True` to re-fetch.

**Data flow:** StatsBomb API → `data_preprocessing.py` → pickle/parquet files in `assets/data/` → `common.py` loads at startup → `app.py` serves UI → user selects match → `utils.py` generates music21 stream → FluidSynth → WAV file → HTML audio player.

## Key Conventions

- Instrument classes are instantiated via `eval('instrument.%s()' % name)` — instrument names in DRUM_INSTRUMENTS and MAIN_INSTRUMENTS must be valid music21 instrument class names.
- Event data is stored as individual parquet files per match: `assets/data/events/events_match{match_id}.parquet`.
- Generated WAV files go to `assets/tmp-wav-{timestamp}.wav` and are cleaned up before each new generation.
- Note durations derive from event duration divided by 5; tempo is fixed at 120 BPM.
- The Procfile references `app:server` (the Flask server exposed by Dash at `app.py:146`).
