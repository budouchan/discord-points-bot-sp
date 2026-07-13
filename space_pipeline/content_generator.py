"""文字起こしテキストから各種コンテンツを生成するモジュール。

生成物:
- 要約 (summary.md)
- X投稿・ブドキン形式 (x_post.md)
- Threads投稿 (threads_post.md)
- ハッシュタグ (hashtags.md)
- 切り抜き候補 (clips.md + clips.json) ※動画生成にも使用
- YouTube概要欄 (youtube_description.md)
- WordPress用ブログ記事 (wordpress.json + blog.html + blog.md)
- Discord用まとめ (discord_post.md)

すべてまとめた all_content.md も出力する。
"""

import json
import re
from datetime import datetime
from pathlib import Path

from openai import OpenAI

from . import config
from .transcriber import format_timestamp

SYSTEM_PROMPT = (
    "あなたはX(Twitter)スペース番組『{show}』を担当する優秀なコンテンツ編集者です。"
    "文字起こしテキストをもとに、依頼されたコンテンツを日本語で作成してください。"
    "話者の雰囲気や配信の温度感を保ちつつ、それぞれの媒体に最適な形式で出力してください。"
    "文字起こしに含まれない情報を捏造しないでください。"
    "不明な項目は「(不明)」と書いてください。"
)

WEEKDAY_JA = ["月", "火", "水", "木", "金", "土", "日"]

# モデルに渡す文字起こしの最大文字数(超えた場合は先頭と末尾を残して中間を間引く)
MAX_TRANSCRIPT_CHARS = 200_000


def _truncate(text: str) -> str:
    if len(text) <= MAX_TRANSCRIPT_CHARS:
        return text
    half = MAX_TRANSCRIPT_CHARS // 2
    return text[:half] + "\n\n...(中略)...\n\n" + text[-half:]


def _weekday_personality(now: datetime) -> str:
    """WEEKDAY_PERSONALITIES(「月:名前,火:名前」形式)から今日の担当を返す。"""
    mapping = {}
    for pair in config.WEEKDAY_PERSONALITIES.split(","):
        if ":" in pair:
            day, name = pair.split(":", 1)
            mapping[day.strip()] = name.strip()
    return mapping.get(WEEKDAY_JA[now.weekday()], "")


def parse_timestamp(value: str) -> float:
    """'HH:MM:SS' / 'MM:SS' 形式の文字列を秒に変換する。"""
    parts = [int(p) for p in re.findall(r"\d+", value)]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    if len(parts) == 1:
        return float(parts[0])
    raise ValueError(f"タイムスタンプを解釈できません: {value!r}")


class ContentGenerator:
    def __init__(self):
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.system_prompt = SYSTEM_PROMPT.format(show=config.SHOW_NAME)

    def _chat(self, prompt: str, source: str, json_mode: bool = False) -> str:
        kwargs = {}
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        response = self.client.chat.completions.create(
            model=config.GPT_MODEL,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {
                    "role": "user",
                    "content": f"{prompt}\n\n--- 文字起こし ---\n{_truncate(source)}",
                },
            ],
            **kwargs,
        )
        return (response.choices[0].message.content or "").strip()

    def _chat_json(self, prompt: str, source: str) -> dict:
        raw = self._chat(prompt, source, json_mode=True)
        return json.loads(raw)

    # ===== 各コンテンツの生成 =====

    def summary(self, transcript: str) -> str:
        return self._chat(
            "このスペースの内容を要約してください。"
            "冒頭に3〜5行の箇条書きで要点をまとめ、"
            "その後に400〜600字程度の文章で全体をまとめてください。",
            transcript,
        )

    def x_post_budokin(self, transcript: str, now: datetime) -> str:
        """ブドキン形式のX投稿を生成する。"""
        date_str = f"{now.year}年{now.month}月{now.day}日({WEEKDAY_JA[now.weekday()]})"
        mc = config.MC_NAME or "(文字起こしから推定してください)"
        personality = _weekday_personality(now) or "(文字起こしから推定してください)"
        recording = config.RECORDING_URL or "(録音URLをここに)"
        prompt = (
            f"番組『{config.SHOW_NAME}』の告知X投稿を、以下のテンプレート形式で1つ作成してください。\n"
            "各項目を文字起こしの内容から埋めてください。テンプレートの構造・項目名・順番は変えないでください。\n"
            "「本日のトピック」は箇条書き2〜4行、その他は1行で簡潔に。\n"
            "ゲストがいない回は「ゲスト」を「なし」としてください。\n"
            "「幻のごじゃトークン」は番組内でその話題が出た場合に内容を書き、出なければ「(なし)」としてください。\n"
            "\n"
            "--- テンプレート ---\n"
            f"【タイトル】(この回の内容を表すキャッチーな一言)\n"
            "\n"
            f"📅 {date_str}\n"
            f"🎙 MC:{mc}\n"
            f"🗓 曜日パーソナリティ:{personality}\n"
            "\n"
            "📌 本日のトピック\n"
            "・\n"
            "・\n"
            "\n"
            "👥 ゲスト:\n"
            "🪙 幻のごじゃトークン:\n"
            "\n"
            f"🎧 録音はこちら\n{recording}\n"
            "\n"
            f"{config.DEFAULT_HASHTAGS} (+内容に合うタグを1〜2個)\n"
            "--- テンプレートここまで ---"
        )
        return self._chat(prompt, transcript)

    def threads_post(self, transcript: str) -> str:
        return self._chat(
            "このスペースの内容を紹介するThreads投稿を2パターン作成してください。"
            "各投稿は500字以内で、Xよりも少しカジュアルで会話的なトーンにしてください。",
            transcript,
        )

    def hashtags(self, transcript: str) -> str:
        return self._chat(
            "このスペースの内容に合うハッシュタグを10〜15個提案してください。"
            "「定番(リーチ狙い)」「ニッチ(関連性重視)」に分類して一覧にしてください。"
            f"必須タグ: {config.DEFAULT_HASHTAGS}",
            transcript,
        )

    def clips(self, timestamped: str) -> list[dict]:
        """切り抜き候補をJSONで生成する。動画・字幕生成にもこの結果を使う。"""
        data = self._chat_json(
            "タイムスタンプ付きの文字起こしから、切り抜き動画に適した場面を5〜8個選び、"
            "JSONで出力してください。形式は次の通り:\n"
            '{"clips": [{"start": "HH:MM:SS", "end": "HH:MM:SS", '
            '"title": "キャッチーな切り抜きタイトル", "reason": "選んだ理由"}]}\n'
            "start/end は文字起こしの実際のタイムスタンプを使い、"
            "各切り抜きは30秒〜3分程度にしてください。",
            timestamped,
        )
        clips = data.get("clips", [])
        # タイムスタンプを秒に変換して検証する(不正なものは除外)
        valid = []
        for c in clips:
            try:
                start = parse_timestamp(str(c["start"]))
                end = parse_timestamp(str(c["end"]))
            except (KeyError, ValueError):
                continue
            if end <= start:
                continue
            valid.append({
                "start": start,
                "end": end,
                "title": str(c.get("title", "")).strip(),
                "reason": str(c.get("reason", "")).strip(),
            })
        return valid

    def youtube_description(self, timestamped: str) -> str:
        return self._chat(
            "このスペースのアーカイブ動画用のYouTube概要欄を作成してください。"
            "構成: 導入文(2〜3行)、主なトピックのタイムスタンプ一覧、関連ハッシュタグ。"
            "タイムスタンプはタイムスタンプ付き文字起こしの実際の時刻を使ってください。",
            timestamped,
        )

    def wordpress(self, transcript: str) -> dict:
        """WordPress投稿用のデータ(title/slug/excerpt/html/tags/category)を生成する。"""
        data = self._chat_json(
            "このスペースの内容をもとに、WordPressにそのまま投稿できるブログ記事を"
            "JSONで出力してください。形式は次の通り:\n"
            "{\n"
            '  "title": "SEOを意識した記事タイトル",\n'
            '  "slug": "english-url-slug",\n'
            '  "excerpt": "記事の抜粋(100〜150字)",\n'
            '  "html": "記事本文のHTML。<h2>見出しごとに構成し、2000〜3000字程度",\n'
            '  "tags": ["タグ1", "タグ2"],\n'
            f'  "category": "{config.WP_DEFAULT_CATEGORY}"\n'
            "}\n"
            "本文は会話の書き起こしではなく、読み物として再構成してください。"
            "HTMLは <h2>, <p>, <ul>, <li>, <strong> のみ使用してください。",
            transcript,
        )
        data.setdefault("category", config.WP_DEFAULT_CATEGORY)
        data.setdefault("tags", [])
        return data

    def discord_post(self, transcript: str) -> str:
        """Discord用まとめをテンプレート形式で生成する。"""
        return self._chat(
            "このスペースの内容を、Discordに投稿する「今日のまとめ」として"
            "以下のテンプレート形式で作成してください。構造は変えないでください。\n"
            "まとめは3〜6個の箇条書き。「明日のテーマ」は番組内で言及があればそれを、"
            "なければ今日の内容から自然につながるテーマを1つ提案してください。\n"
            "\n"
            "--- テンプレート ---\n"
            "## 今日のまとめ\n"
            "\n"
            "・\n"
            "・\n"
            "・\n"
            "\n"
            "**明日のテーマ**\n"
            "(テーマ)\n"
            "--- テンプレートここまで ---",
            transcript,
        )


def render_clips_md(clips: list[dict]) -> str:
    lines = []
    for i, c in enumerate(clips, 1):
        lines.append(
            f"## {i}. {c['title']}\n\n"
            f"- 区間: {format_timestamp(c['start'])}{format_timestamp(c['end'])}\n"
            f"- 理由: {c['reason']}\n"
        )
    return "\n".join(lines) if lines else "(切り抜き候補なし)"


def generate_all(
    transcript: str,
    segments: list[dict],
    output_dir: Path,
    now: datetime | None = None,
) -> dict:
    """全コンテンツを生成して output_dir に保存し、生成結果の辞書を返す。

    返り値: {"clips": [...], "wordpress": {...}, "discord": str, "combined_path": Path}
    """
    now = now or datetime.now()
    gen = ContentGenerator()
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamped = "\n".join(
        f"[{format_timestamp(s['start'])}] {s['text']}" for s in segments
    )

    outputs: list[tuple[str, str, str]] = []  # (見出し, ファイル名, 本文)

    print("生成中: 要約 ...")
    outputs.append(("要約", "summary.md", gen.summary(transcript)))

    print(f"生成中: X投稿({config.SHOW_NAME}形式) ...")
    outputs.append(("X投稿", "x_post.md", gen.x_post_budokin(transcript, now)))

    print("生成中: Threads投稿 ...")
    outputs.append(("Threads投稿", "threads_post.md", gen.threads_post(transcript)))

    print("生成中: ハッシュタグ ...")
    outputs.append(("ハッシュタグ", "hashtags.md", gen.hashtags(transcript)))

    print("生成中: 切り抜き候補 ...")
    clips = gen.clips(timestamped)
    (output_dir / "clips.json").write_text(
        json.dumps(clips, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    outputs.append(("切り抜き候補", "clips.md", render_clips_md(clips)))

    print("生成中: YouTube概要欄 ...")
    outputs.append(("YouTube概要欄", "youtube_description.md", gen.youtube_description(timestamped)))

    print("生成中: WordPress記事 ...")
    wp = gen.wordpress(transcript)
    (output_dir / "wordpress.json").write_text(
        json.dumps(wp, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output_dir / "blog.html").write_text(wp.get("html", ""), encoding="utf-8")
    blog_md = (
        f"# {wp.get('title', '')}\n\n"
        f"- slug: `{wp.get('slug', '')}`\n"
        f"- category: {wp.get('category', '')}\n"
        f"- tags: {', '.join(wp.get('tags', []))}\n\n"
        f"> {wp.get('excerpt', '')}\n\n"
        f"(本文HTMLは blog.html / wordpress.json を参照)\n"
    )
    outputs.append(("ブログ記事(WordPress)", "blog.md", blog_md))

    print("生成中: Discord用まとめ ...")
    discord_text = gen.discord_post(transcript)
    outputs.append(("Discord用まとめ", "discord_post.md", discord_text))

    combined_parts = []
    for heading, filename, content in outputs:
        (output_dir / filename).write_text(f"# {heading}\n\n{content}\n", encoding="utf-8")
        combined_parts.append(f"# {heading}\n\n{content}")

    combined_path = output_dir / "all_content.md"
    combined_path.write_text("\n\n---\n\n".join(combined_parts) + "\n", encoding="utf-8")
    print(f"コンテンツ生成完了: {combined_path}")

    return {
        "clips": clips,
        "wordpress": wp,
        "discord": discord_text,
        "combined_path": combined_path,
    }
