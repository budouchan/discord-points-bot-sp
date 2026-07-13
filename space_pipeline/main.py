"""後方互換のためのエントリポイント。

現在は `space` コマンド(cli.py)がメインの入口。
`python -m space_pipeline.main` は `space start` 相当として動作する。
"""

import sys

from .cli import main as cli_main


def main() -> None:
    # 旧: `python -m space_pipeline.main --input x` → 新: `space start --input x`
    if len(sys.argv) < 2 or sys.argv[1].startswith("-"):
        sys.argv.insert(1, "start")
    cli_main()


if __name__ == "__main__":
    main()
