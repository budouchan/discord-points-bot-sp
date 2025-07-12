# ------------------------------------------------
# discord-points-bot-sp/bot.py - 完成版
# ------------------------------------------------
import os
import logging
from datetime import datetime, timezone, timedelta

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
from sqlalchemy.orm import Session

# モジュール読み込み
from database import SessionLocal, init_db, get_db_info
from models import Transaction, User
from utils import (TARGET_GUILD, AUTHORIZED, EMOJI_POINTS, 
                   format_ranking_message, SERVER_NAMES, format_status_ranking)

# ─── 初期設定 ─────────────────────────────────────

# .envファイルから環境変数を読み込む
load_dotenv()

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)-8s %(message)s')

# Discord Botの準備
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.guilds = True
intents.members = True # メンバー情報を取得するために必要

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# ─── イベントハンドラ ────────────────────────────────

@bot.event
async def on_ready():
    """ボットの準備が完了したときに呼ばれるイベント"""
    logging.info("--------------------------------------------------")
    logging.info(f"✅ Bot is ready! Logged in as: {bot.user.name}")
    logging.info(f"✅ Bot ID: {bot.user.id}")
    logging.info("--------------------------------------------------")

    # バックグラウンドタスクを開始
    if not update_status_task.is_running():
        logging.info("🚀 Starting background task: update_status_task")
        update_status_task.start()

@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    """リアクションが追加されたときに呼ばれるイベント"""
    # ボット自身のリアクションは無視
    if payload.user_id == bot.user.id:
        return

    # 対象のサーバーか確認
    if payload.guild_id != TARGET_GUILD:
        return

    emoji_str = str(payload.emoji)

    # ポイント対象の絵文字か確認
    if emoji_str not in EMOJI_POINTS:
        return

    points = EMOJI_POINTS[emoji_str]

    try:
        db: Session = next(get_db())

        # メッセージの投稿者を取得
        channel = bot.get_channel(payload.channel_id)
        if not isinstance(channel, discord.TextChannel): return

        message = await channel.fetch_message(payload.message_id)
        author_id = message.author.id

        # 自分自身へのリアクションは無効
        if author_id == payload.user_id:
            logging.info(f"Self-reaction ignored: {payload.member.name} on own message.")
            return

        # ユーザー情報をDBに登録（なければ）
        user = db.query(User).filter(User.id == author_id).first()
        if not user:
            user = User(id=author_id, name=message.author.name)
            db.add(user)
            db.commit()
            db.refresh(user)
            logging.info(f"New user created: {user.name} ({user.id})")

        # ポイントを追加
        new_transaction = Transaction(
            user_id=author_id,
            points=points,
            reason=f"Reaction by {payload.member.display_name} with {emoji_str}"
        )
        db.add(new_transaction)
        db.commit()

        logging.info(f"✅ Points added: {points}pt to {message.author.name} for emoji {emoji_str}")

    except Exception as e:
        logging.error(f"Error in on_raw_reaction_add: {e}", exc_info=True)
    finally:
        if db:
            db.close()

# ─── コマンド ───────────────────────────────────────

@bot.command(name="ranking")
async def show_ranking(ctx: commands.Context):
    """現在のランキングを表示するコマンド"""
    # TODO: ランキング表示機能の実装
    await ctx.send("ランキング機能は現在準備中です。")

# ─── バックグラウンドタスク ──────────────────────────

@tasks.loop(minutes=1)
async def update_status_task():
    """ボットのステータスを定期的に更新するタスク"""
    await bot.wait_until_ready()
    try:
        # TODO: ランキングデータを取得してステータスを更新する
        status_text = "🏆 ランキング集計中..."
        activity = discord.Game(name=status_text)
        await bot.change_presence(status=discord.Status.online, activity=activity)
        logging.info(f"Status updated: {status_text}")
    except Exception as e:
        logging.error(f"Error in update_status_task: {e}", exc_info=True)


# ─── 起動 ─────────────────────────────────────────

if __name__ == "__main__":
    try:
        logging.info("🚀 Bot起動開始")
        # データベースの初期化
        init_db()

        token = os.getenv('DISCORD_TOKEN')
        if not token:
            raise ValueError("DISCORD_TOKEN not found in .env file")

        bot.run(token)

    except Exception as e:
        logging.error(f"❌ ボットの起動に失敗しました: {e}", exc_info=True)