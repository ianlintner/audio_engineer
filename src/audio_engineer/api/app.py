"""FastAPI application factory for the AI Music Studio."""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Music Studio",
        version="0.1.0",
        description="Multi-agent system for generating MIDI backing tracks",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # MVP only
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from audio_engineer.api.routes import sessions, tracks, exports

    app.include_router(sessions.router, prefix="/api/sessions", tags=["sessions"])
    app.include_router(tracks.router, prefix="/api/tracks", tags=["tracks"])
    app.include_router(exports.router, prefix="/api/exports", tags=["exports"])

    @app.get("/api/health")
    def health():
        return {"status": "ok", "version": "0.1.0"}

    # Serve static UI files (must be last — catch-all mount)
    static_dir = Path(__file__).parent.parent / "ui" / "static"
    if static_dir.exists():
        app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")

    return app
