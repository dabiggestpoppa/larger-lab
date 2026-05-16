# 🎻 Violin — Video Translation Skill

Open-source video translation tool. Transcribes speech, translates it, synthesizes native-sounding voice-over, and remuxes back into the video.

**Use Violin when:**
- User wants to translate/dub a video into another language
- User wants to generate subtitles (SRT) for a video
- User wants voice-over in a target language

**Requires:** Python 3.10+, `violin` CLI, `ffmpeg` on PATH, `TOGETHER_API_KEY`

## Quick Start

```bash
# Translate a video to Chinese
violin lecture.mp4 lecture_zh.mp4 --language Chinese

# Translate with style
violin talk.mp4 talk_es.mp4 --language Spanish --style academic

# Pick a specific voice
violin lecture.mp4 lecture_fr.mp4 --language French --voice "french narrator man"

# Skip SRT generation
violin lecture.mp4 lecture_ja.mp4 --language Japanese --no-subtitles

# Full audio replacement (no original audio underneath)
violin lecture.mp4 lecture_ko.mp4 --language Korean --no-voiceover
```

## CLI Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--language` / `-l` | *(required)* | Target language (e.g. `Chinese`, `Spanish`, `Japanese`) |
| `--voice` / `-v` | auto | TTS voice. Defaults to native voice for target language |
| `--source-language` | `auto-detect` | Source language hint |
| `--style` / `-s` | `standard` | Style profile (see below) |
| `--no-subtitles` | off | Skip SRT generation |
| `--no-voiceover` | off | Replace original audio entirely |
| `--config` / `-c` | default YAML | Custom config (advanced) |
| `--timings-out` | off | Write per-step timing JSON |

## Style Profiles

| Style | Tone | TTS Speed | Emotion |
|-------|------|-----------|---------|
| `standard` | Faithful, natural | 1.0× | — |
| `kids` | Plain language, 7-year-old level | 1.0× | excited |
| `academic` | Formal, preserves jargon | 0.95× | calm |
| `casual` | Slang, contractions, friendly | 1.1× | content |
| `storyteller` | Vivid, dramatic | 0.9× | enthusiastic |
| `news` | Concise, broadcast-style | 1.0× | neutral |

List all styles: `violin --style list`

## Supported Languages

**33 target languages total.** 16 have handpicked native-speaker voices:
Chinese, Spanish, English, Hindi, Arabic, Portuguese, Russian, Japanese, Turkish, German, Korean, French, Italian, Polish, Dutch, Swedish.

17 fallback languages (use English voice catalog): Vietnamese, Tamil, Indonesian, Malay, Ukrainian, Romanian, Thai, Greek, Hungarian, Catalan, Czech, Bulgarian, Danish, Slovak, Croatian, Finnish, Norwegian.

## Web App / REST API

```bash
violin-api                              # Start server
violin-api --host 0.0.0.0 --port 8080   # Custom bind
```

- `POST /jobs` — Submit translation job
- `GET /jobs/{id}` — Poll status
- `GET /jobs/{id}/video` — Download dubbed video
- `GET /jobs/{id}/srt` — Download subtitles
- `POST /jobs/{id}/chat` — In-video Q&A
- `/docs` — Interactive API docs

## Pipeline

```
Video → ffmpeg (extract audio) → Whisper (transcribe) → LLM (translate) → TTS (synthesize) → ffmpeg (remux)
```

Default stack: Together AI (DeepSeek V4 Pro) for translation, Cartesia Sonic 3 for TTS.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `TOGETHER_API_KEY` | **Yes** (default config) | Together AI API key |
| `OPENAI_API_KEY` | If using OpenAI provider | OpenAI API key |
| `ELEVENLABS_API_KEY` | If using ElevenLabs TTS | ElevenLabs API key |

## Links

- **GitHub:** https://github.com/shang-zhu/violin
- **Demo:** https://www.violin-ai.com
- **License:** MIT
