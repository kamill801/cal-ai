"""Local-only preview of the Vercel API + exported Expo route arrangement."""

from pathlib import Path

from starlette.staticfiles import StaticFiles

from app.main import app


app.mount("/", StaticFiles(directory=Path(__file__).resolve().parents[2] / "public"), name="local-web-preview")
