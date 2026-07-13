"""生成したコンテンツを外部へ書き出すモジュール。

- Obsidian: Vaultに「YYYY-MM-DD ブドキン.md」として保存
- Discord: Webhook URLが設定されていればまとめを自動投稿
"""

import json
import urllib.request
from datetime import datetime
from pathlib import Path

from . import config

DISCORD_CHAR_LIMIT = 2000


def save_to_obsidian(combined_path: Path, now: datetime | None = None) -> Path | None:
    """all_content.md をObsidian Vaultにデイリーノートとして保存する。

    OBSIDIAN_VAULT_DIR が未設定、またはディレクトリが存在しない場合はスキップ。
    """
    if not config.OBSIDIAN_VAULT_DIR:
        print("Obsidian: OBSIDIAN_VAULT_DIR が未設定のためスキップします。")
        return None
    vault = Path(config.OBSIDIAN_VAULT_DIR).expanduser()
    if not vault.is_dir():
        print(f"Obsidian: Vaultが見つかりません({vault})。スキップします。")
        return None

    now = now or datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    note_path = vault / f"{date_str} {config.SHOW_NAME}.md"

    frontmatter = (
        "---\n"
        f"date: {date_str}\n"
        f"show: {config.SHOW_NAME}\n"
        "tags:\n"
        f"  - {config.SHOW_NAME}\n"
        "  - スペース\n"
        "---\n\n"
    )
    note_path.write_text(
        frontmatter + combined_path.read_text(encoding="utf-8"), encoding="utf-8"
    )
    print(f"Obsidianに保存しました: {note_path}")
    return note_path


def post_to_discord(text: str) -> bool:
    """Discord Webhookにまとめを投稿する。URL未設定ならスキップ。"""
    if not config.DISCORD_WEBHOOK_URL:
        print("Discord: DISCORD_WEBHOOK_URL が未設定のため投稿をスキップします"
              "(discord_post.md は生成済み)。")
        return False

    content = text.strip()
    if len(content) > DISCORD_CHAR_LIMIT:
        content = content[: DISCORD_CHAR_LIMIT - 20] + "\n…(以下略)"

    payload = json.dumps({"content": content}).encode("utf-8")
    request = urllib.request.Request(
        config.DISCORD_WEBHOOK_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as res:
            if 200 <= res.status < 300:
                print("Discordに投稿しました。")
                return True
            print(f"Discord投稿に失敗しました (HTTP {res.status})")
    except Exception as e:  # 投稿失敗でもパイプライン全体は止めない
        print(f"Discord投稿に失敗しました: {e}")
    return False
