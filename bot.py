import os
import logging
from datetime import datetime, timezone

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from database import SessionLocal, init_db, get_db
from models import Transaction, User
from utils import (TARGET_GUILDS, AUTHORIZED_USERS, SERVER_EMOJI_POINTS,
                   SERVER_NAMES, format_ranking_message, format_status_ranking)

# ─── 初期設定 ─────────────────────────────────────
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)-8s %(message)s')

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# ─── イベントハンドラ ────────────────────────────────

@bot.event
async def on_ready():
    """ボットの準備が完了したときに呼ばれるイベント"""
    logging.info("--------------------------------------------------")
    logging.info(f"✅ Bot is ready! Logged in as: {bot.user.name}")
    logging.info(f"✅ Bot ID: {bot.user.id}")
    logging.info(f"✅ Watching {len(bot.guilds)} servers.")
    logging.info("--------------------------------------------------")

    # バックグラウンドタスクを開始
    if not update_status_task.is_running():
        logging.info("🚀 Starting background task: update_status_task")
        update_status_task.start()

@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    """リアクションが追加されたときに呼ばれるイベント"""
    if payload.guild_id not in TARGET_GUILDS or payload.user_id == bot.user.id:
        return

    guild_id = payload.guild_id
    emoji_str = str(payload.emoji)

    # このサーバーのポイント対象絵文字か確認
    if emoji_str not in SERVER_EMOJI_POINTS.get(guild_id, {}):
        return

    points = SERVER_EMOJI_POINTS[guild_id][emoji_str]

    db: Session = next(get_db())
    try:
        channel = bot.get_channel(payload.channel_id)
        if not isinstance(channel, discord.TextChannel): return

        message = await channel.fetch_message(payload.message_id)
        author = message.author

        if author.id == payload.user_id:
            return

        # ユーザー情報をDBに登録（なければ）
        user = db.query(User).filter(User.id == author.id).first()
        if not user:
            user = User(id=author.id, name=author.name)
            db.add(user)
            db.commit()

        # ポイントを記録
        new_transaction = Transaction(
            user_id=author.id,
            guild_id=guild_id,
            points=points,
            reason=f"Reaction by user_id {payload.user_id} with {emoji_str}",
            message_timestamp=message.created_at
        )
        db.add(new_transaction)
        db.commit()

        logging.info(f"✅ Points added: {points}pt to {author.name} in guild {guild_id}")

    except Exception as e:
        logging.error(f"Error in on_raw_reaction_add: {e}", exc_info=True)
    finally:
        db.close()

@bot.event
async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent):
    """リアクションが削除されたときに呼ばれるイベント"""
    if payload.guild_id not in TARGET_GUILDS:
        return

    guild_id = payload.guild_id
    emoji_str = str(payload.emoji)

    if emoji_str not in SERVER_EMOJI_POINTS.get(guild_id, {}):
        return

    points_to_deduct = -SERVER_EMOJI_POINTS[guild_id][emoji_str]

    db: Session = next(get_db())
    try:
        channel = bot.get_channel(payload.channel_id)
        if not isinstance(channel, discord.TextChannel): return

        message = await channel.fetch_message(payload.message_id)
        author = message.author

        # ポイントを減算
        new_transaction = Transaction(
            user_id=author.id,
            guild_id=guild_id,
            points=points_to_deduct,
            reason=f"Reaction removed by user_id {payload.user_id} with {emoji_str}",
            message_timestamp=message.created_at
        )
        db.add(new_transaction)
        db.commit()

        logging.info(f"✅ Points deducted: {abs(points_to_deduct)}pt from {author.name} in guild {guild_id}")

    except Exception as e:
        logging.error(f"Error in on_raw_reaction_remove: {e}", exc_info=True)
    finally:
        db.close()

# ─── コマンド（今後実装） ───────────────────────────────────

@bot.command(name="ranking")
async def show_ranking(ctx: commands.Context):
    await ctx.send("ランキング機能は現在準備中です。")

# ─── バックグラウンドタスク（今後実装） ───────────────────

@tasks.loop(minutes=10)
async def update_status_task():
    await bot.wait_until_ready()
    # TODO: 両サーバーの合計人数などを表示するなど、ステータスを更新する
    status_text = f"2つのサーバーを監視中"
    activity = discord.Game(name=status_text)
    await bot.change_presence(status=discord.Status.online, activity=activity)

# ─── 起動 ─────────────────────────────────────────

if __name__ == "__main__":
    try:
        logging.info("🚀 Bot起動開始")
        init_db()

        token = os.getenv('DISCORD_TOKEN')
        if not token:
            raise ValueError("DISCORD_TOKEN not found in .env file")

        bot.run(token)

    except Exception as e:
        logging.error(f"❌ ボットの起動に失敗しました: {e}", exc_info=True)