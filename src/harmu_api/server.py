"""服务启动入口。"""

from __future__ import annotations

import argparse

import uvicorn

from .api import create_app


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Harmu 回合制对决服务端")
    parser.add_argument("--host", default="127.0.0.1", help="监听地址")
    parser.add_argument("--port", type=int, default=8000, help="监听端口")
    args = parser.parse_args(argv)
    uvicorn.run(create_app(), host=args.host, port=args.port)


if __name__ == "__main__":
    main()
