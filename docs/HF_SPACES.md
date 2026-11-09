# Hugging Face Spaces — full app (Docker)

Visitors get:
1. **Kuku Sample Show (demo)** — full hybrid outputs for all 50 assignment episodes (scripts not included)
2. **New project → upload .txt scripts → Generate** — fully usable for other shows

## Create the Space

1. https://huggingface.co/new-space  
2. **SDK = Docker** · public  
3. Link GitHub repo `krshailendra/KuKu-Round-2` **or** push this repo to the Space git remote  
4. Space settings → **Secrets**:
   - `GROQ_API_KEY` = your key (needed for Hybrid polish; rule mode works without it)
5. Variables (optional, Dockerfile already defaults):
   - `DEMO_PUBLIC=1`
   - `DEMO_MAX_EPISODES=50`
   - `DEMO_DEFAULT_MODE=hybrid`
6. Wait for build → open `https://huggingface.co/spaces/<you>/kuku-promo-finder`

App port: **7860** (Dockerfile default).

## Cold starts

Free CPU Spaces **sleep when idle**. First open after sleep can take ~30–60s — then the app is fully interactive.  
There is no free always-on FastAPI host; static-only would skip Generate.

## What is NOT on the Space

- Assignment episode `.txt` scripts (gitignored)
- Your `.env` file

Seed demo results live under `data/projects/e3226269c4/output/` and load on boot.
