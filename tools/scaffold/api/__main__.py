import os

import uvicorn

from tools.scaffold.api.main import app


def main() -> None:
    host = os.getenv("SCAFFOLD_API_HOST", "0.0.0.0")
    port = int(os.getenv("SCAFFOLD_API_PORT", "8001"))
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
