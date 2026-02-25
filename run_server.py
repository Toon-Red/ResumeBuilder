"""Entry point for the Resume Builder server."""

import argparse
import json
from pathlib import Path

import uvicorn

from server.api import app, init_app


def main():
    parser = argparse.ArgumentParser(description="Resume Builder Server")
    parser.add_argument("--port", type=int, default=None, help="Port to run on")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--config", type=str, default="config.json", help="Config file path")
    args = parser.parse_args()

    base_dir = Path(__file__).parent
    config_path = base_dir / args.config
    config = json.loads(config_path.read_text(encoding="utf-8"))

    port = args.port or config.get("port", 8080)

    init_app(config, base_dir)

    print(f"Resume Builder starting on http://{args.host}:{port}")
    uvicorn.run(app, host=args.host, port=port)


if __name__ == "__main__":
    main()
