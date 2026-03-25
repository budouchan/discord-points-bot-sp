import discord
from discord.ext import tasks
import asyncio
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, BigInteger, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
from utils import *

# データベース設定
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# データベースモデル
class User(Base):
    __tablename__ = "users"
    
    id = Column(BigInteger, primary_key=True)
    username = Column(String, nullable=False)
    
    transactions = relationship("Transaction", back_populates="user")

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    guild_id = Column(BigInteger, nullable=False)
    points = Column(Integer, nullable=False)
    reason = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    message_timestamp = Column(DateTime, nullable=True)
    
    user = relationship("User", back_populates="transactions")

# テーブル作成
def init_db():
    print("📊 PostgreSQLテーブル作成中...")
    Base.metadata.create_all(bind=engine)
    # usersテーブルにusernameカラムが無ければ追加
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS username VARCHAR"))
            conn.commit()
            print("✅ usernameカラム確認・追加完了")
        except Exception as e:
            print(f"カラム追加スキップ: {e}")
    print("✅ PostgreSQLテーブル作成完了")

def get_or_create_user(db, user_id: int, username: str):
    """ユーザーを取得、存在しなければ作成"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        user = User(id=user_id, username=username)
        db.add(user)
        db.commit()
        print(f"👤 新規ユーザー登録: {username} (ID: {user_id})")
    return user

def add_points(user_id: int, username: str, guild_id: int, points: int, reason: str, message_timestamp=None):
    db = SessionLocal()
    try:
        # ユーザーを取得または作成
        user = get_or_create_user(db, user_id, username)
        
        transaction = Transaction(
            user_id=user_id,
            guild_id=guild_id,
            points=points,
            reason=reason,
            message_timestamp=message_timestamp
        )
        db.add(transaction)
        db.commit()
        
        # 現在のポイント合計を計算
        total_points = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.guild_id == guild_id
        ).with_entities(
            Transaction.points
        ).all()
        
        current_total = sum(t[0] for t in total_points)
        
        server_name = SERVER_NAMES.get(guild_id, f'Guild {guild_id}')
        if points > 0:
            print(f"✅ Points added: {points}pt to {username} in guild {guild_id}")
        else:
            print(f"✅ Points deducted: {abs(points)}pt from {username} in guild {guild_id}")
            
        return current_total
    except Exception as e:
        db.rollback()
        print(f"❌ Error adding points: {e}")
        return None
    finally:
        db.close()

def get_ranking(guild_id: int, limit: int = 10):
    db = SessionLocal()
    try:
        from sqlalchemy import func
        ranking = db.query(
            User.username,
            func.sum(Transaction.points).label('total_points')
        ).join(Transaction).filter(
            Transaction.guild_id == guild_id
        ).group_by(User.id, User.username).order_by(
            func.sum(Transaction.points).desc()
        ).limit(limit).all()
        
        return [(username, int(total_points)) for username, total_points in ranking]
    finally:
        db.close()

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.guilds = True

bot = discord.Bot(intents=intents)

@bot.event
async def on_ready():
    print("--" * 25)
    print(f"✅ Bot is ready! Logged in as: {bot.user}")
    print(f"✅ Bot ID: {bot.user.id}")
    print(f"✅ Watching {len(TARGET_GUILDS)} servers.")
    print("--" * 25)
    
    update_status_task.start()

@bot.event
async def on_raw_reaction_add(payload):
    if payload.guild_id not in TARGET_GUILDS:
        return
    
    if payload.user_id == bot.user.id:
        return
    
    emoji_str = str(payload.emoji)
    guild_emoji_points = SERVER_EMOJI_POINTS.get(payload.guild_id, {})
    
    if emoji_str in guild_emoji_points:
        points = guild_emoji_points[emoji_str]
        
        # ユーザー情報を取得
        user = bot.get_user(payload.user_id)
        username = user.display_name if user else f"User_{payload.user_id}"
        
        # メッセージのタイムスタンプを取得
        try:
            channel = bot.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            message_timestamp = message.created_at
        except:
            message_timestamp = datetime.utcnow()
        
        reason = f"Reaction by user_id {payload.user_id} with {emoji_str}"
        
        current_total = add_points(
            payload.user_id, 
            username, 
            payload.guild_id, 
            points, 
            reason,
            message_timestamp
        )

@bot.event
async def on_raw_reaction_remove(payload):
    if payload.guild_id not in TARGET_GUILDS:
        return
    
    if payload.user_id == bot.user.id:
        return
    
    emoji_str = str(payload.emoji)
    guild_emoji_points = SERVER_EMOJI_POINTS.get(payload.guild_id, {})
    
    if emoji_str in guild_emoji_points:
        points = guild_emoji_points[emoji_str]
        
        # ユーザー情報を取得
        user = bot.get_user(payload.user_id)
        username = user.display_name if user else f"User_{payload.user_id}"
        
        # メッセージのタイムスタンプを取得
        try:
            channel = bot.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            message_timestamp = message.created_at
        except:
            message_timestamp = datetime.utcnow()
        
        reason = f"Reaction removed by user_id {payload.user_id} with {emoji_str}"
        
        current_total = add_points(
            payload.user_id, 
            username, 
            payload.guild_id, 
            -points, 
            reason,
            message_timestamp
        )

@bot.slash_command(name="ranking", description="ポイントランキングを表示します")
async def ranking_command(ctx):
    if ctx.guild_id not in TARGET_GUILDS:
        await ctx.respond("このサーバーではポイント機能は利用できません。", ephemeral=True)
        return
    
    rankings = get_ranking(ctx.guild_id)
    
    if not rankings:
        await ctx.respond("まだランキングデータがありません。", ephemeral=True)
        return
    
    server_name = SERVER_NAMES.get(ctx.guild_id, 'サーバー')
    current_time = datetime.now().strftime('%m/%d %H:%M')
    
    try:
        message = await format_ranking_message(server_name, rankings, current_time)
        await ctx.respond(message)
    except Exception as e:
        print(f"❌ Error in ranking command: {e}")
        await ctx.respond("ランキング表示中にエラーが発生しました。", ephemeral=True)

@bot.slash_command(name="mypoints", description="自分のポイントを確認します")
async def mypoints_command(ctx):
    if ctx.guild_id not in TARGET_GUILDS:
        await ctx.respond("このサーバーではポイント機能は利用できません。", ephemeral=True)
        return
    
    db = SessionLocal()
    try:
        # ユーザーを取得または作成
        user = get_or_create_user(db, ctx.author.id, ctx.author.display_name)
        
        total_points = db.query(Transaction).filter(
            Transaction.user_id == ctx.author.id,
            Transaction.guild_id == ctx.guild_id
        ).with_entities(
            Transaction.points
        ).all()
        
        current_total = sum(t[0] for t in total_points) if total_points else 0
        server_name = SERVER_NAMES.get(ctx.guild_id, 'サーバー')
        
        await ctx.respond(f"🏆 **{server_name}** での{ctx.author.display_name}さんのポイント: **{current_total}pt**")
    finally:
        db.close()

@tasks.loop(minutes=5)
async def update_status_task():
    try:
        all_rankings = []
        for guild_id in TARGET_GUILDS:
            rankings = get_ranking(guild_id, 3)
            for username, points in rankings:
                all_rankings.append((username, points))
        
        all_rankings.sort(key=lambda x: x[1], reverse=True)
        status_text = format_status_ranking(all_rankings[:6])
        
        await bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=status_text
            )
        )
    except Exception as e:
        print(f"❌ Error updating status: {e}")

if __name__ == "__main__":
    print("🚀 Bot起動開始")
    init_db()
    print("🎉 データベース初期化成功")
    
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        print("❌ DISCORD_BOT_TOKENが設定されていません")
        exit(1)
    
    bot.run(token)
