"""Single-command entrypoint for running the Zana webhook server."""

import os
import uvicorn


def main() -> None:
    host = os.getenv("ZANA_HOST", "0.0.0.0")
    port = int(os.getenv("ZANA_PORT", "8000"))
    reload_enabled = os.getenv("ZANA_RELOAD", "true").lower() in {"1", "true", "yes", "on"}

    uvicorn.run(
        "webhook.server:app",
        host=host,
        port=port,
        reload=reload_enabled,
    )


if __name__ == "__main__":
    main()
