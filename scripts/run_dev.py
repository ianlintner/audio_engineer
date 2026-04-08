#!/usr/bin/env python3
"""Start the AI Music Studio development server."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "audio_engineer.api.app:create_app",
        factory=True,
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["src"],
    )
