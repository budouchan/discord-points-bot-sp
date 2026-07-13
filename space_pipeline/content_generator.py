"""文字起こしテキストから各種コンテンツを生成するモジュール。

生成物:
- 要約 (summary.md)
- X投稿 (x_post.md)
- Threads投稿 (threads_post.md)
- ハッシュタグ (hashtags.md)
- 切り抜き候補 (clips.md) ※タイムスタンプ付き文字起こしを使用
- YouTube概要欄 (youtube_description.md)
- ブログ記事 (blog.md)

すべてまとめた all_content.md も出力する。
"""

from pathlib import Path

from openai import OpenAI

from . import config
from .transcriber import format_timestamp

SYSTEM_PROMPT = (
    "あなたはX(Twitter)スペースの音声配信を担当する優秀なコンテンツ編集者です。"
    "文字起こしテキストをもとに、依頼されたコンテンツを日本語で作成してください。"
    "話者の雰囲気や配信の温度感を保ちつつ、それぞれの媒体に最適な形式で出力してください。"
    "文字起こしに含まれない情報を捏造しないでください。"
)

# (キー, 出力ファイル名, 見出し, プロンプト, タイムスタンプ付きを使うか)
TASKS = [
    (
        "summary", "summary.md", "要約",
        "このスペースの内容を要約してください。"
        "冒頭に3〜5行の箇条書きで要点をまとめ、その後に400〜600字程度の文章で全体をまとめてください。",
        False,
    ),
    (
        "x_post", "x_post.md", "X投稿",
        "このスペースの内容を告知・振り返りするX(Twitter)投稿を3パターン作成してください。"
        "各投稿は日本語で140字以内に収め、続きを聞きたくなるフックを入れてください。"
        "ハッシュタグは各投稿に1〜2個まで。",
        False,
    ),
    (
        "threads_post", "threads_post.md", "Threads投稿",
        "このスペースの内容を紹介するThreads投稿を2パターン作成してください。"
        "各投稿は500字以内で、Xよりも少しカジュアルで会話的なトーンにしてください。",
        False,
    ),
    (
        "hashtags", "hashtags.md", "ハッシュタグ",
        "このスペースの内容に合うハッシュタグを10〜15個提案してください。"
        "「定番(リーチ狙い)」「ニッチ(関連性重視)」に分類して一覧にしてください。",
        False,
    ),
    (
        "clips", "clips.md", "切り抜き候補",
        "タイムスタンプ付きの文字起こしから、切り抜き動画に適した場面を5〜8個選んでください。"
        "各候補について以下を出力してください:\n"
        "- 開始〜終了タイムスタンプ\n"
        "- 切り抜きタイトル案(キャッチーに)\n"
        "- 選んだ理由(盛り上がり・学び・意外性など)",
        True,
    ),
    (
        "youtube_description", "youtube_description.md", "YouTube概要欄",
        "このスペースのアーカイブ動画用のYouTube概要欄を作成してください。"
        "構成: 導入文(2〜3行)、主なトピックのタイムスタンプ一覧、関連ハッシュタグ。"
        "タイムスタンプはタイムスタンプ付き文字起こしの実際の時刻を使ってください。",
        True,
    ),
    (
        "blog", "blog.md", "ブログ記事",
        "このスペースの内容をもとに、2000〜3000字程度のブログ記事をMarkdownで書いてください。"
        "SEOを意識したタイトル、導入、見出し(##)ごとの本文、まとめの構成にしてください。"
        "会話の流れをそのまま書き起こすのではなく、読み物として再構成してください。",
        False,
    ),
]

# モデルに渡す文字起こしの最大文字数(超えた場合は先頭と末尾を残して中間を間引く)
MAX_TRANSCRIPT_CHARS = 200_000


def _truncate(text: str) -> str:
    if len(text) <= MAX_TRANSCRIPT_CHARS:
        return text
    half = MAX_TRANSCRIPT_CHARS // 2
    return text[:half] + "\n\n...(中略)...\n\n" + text[-half:]


def generate_all(transcript: str, segments: list[dict], output_dir: Path) -> Path:
    """全コンテンツを生成して output_dir に保存し、まとめファイルのパスを返す。"""
    client = OpenAI(api_key=config.OPENAI_API_KEY)
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamped = "\n".join(
        f"[{format_timestamp(s['start'])}] {s['text']}" for s in segments
    )

    combined_parts: list[str] = []
    for key, filename, heading, prompt, use_timestamps in TASKS:
        print(f"生成中: {heading} ...")
        source = timestamped if use_timestamps else transcript
        response = client.chat.completions.create(
            model=config.GPT_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"{prompt}\n\n"
                        "--- 文字起こし ---\n"
                        f"{_truncate(source)}"
                    ),
                },
            ],
        )
        content = (response.choices[0].message.content or "").strip()
        (output_dir / filename).write_text(f"# {heading}\n\n{content}\n", encoding="utf-8")
        combined_parts.append(f"# {heading}\n\n{content}")

    combined_path = output_dir / "all_content.md"
    combined_path.write_text("\n\n---\n\n".join(combined_parts) + "\n", encoding="utf-8")
    print(f"コンテンツ生成完了: {combined_path}")
    return combined_path
