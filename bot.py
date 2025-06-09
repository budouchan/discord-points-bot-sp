import os
from datetime import datetime
import discord
from discord.ext import commands
from dotenv import load_dotenv
import asyncio
from sqlalchemy import create_engine, Column, Integer, String, DateTime, BigInteger
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.future import select
from typing import AsyncGenerator

# データベース設定
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:////data/database.db")
engine = create_async_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)
Base = declarative_base()

# データベース初期化関数
async def init_db():
    try:
        print("🚀 データベース初期化開始")
        
        # テーブルの作成
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        
        # テーブルの存在確認
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='transactions'"))
            if not result.fetchone():
                raise Exception("transactionsテーブルが作成されませんでした")
            
            # テーブルのカラムを確認
            result = await conn.execute(text("PRAGMA table_info(transactions)"))
            columns = [row[1] for row in result.fetchall()]
            print(f"✅ transactionsテーブルのカラム: {columns}")
            
        print("✅ データベース初期化完了")
        
    except Exception as e:
        print(f"❌ データベース初期化エラー: {e}")
        raise

# トランザクションモデル
class Transaction(Base):
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True, index=True)
    recipient_id = Column(BigInteger, nullable=False)  # ポイントを受け取った人のID
    points_awarded = Column(Integer, nullable=False)   # 与えられたポイント数
    giver_id = Column(BigInteger)                     # ポイントを与えた人のID
    emoji_id = Column(String)                         # 使用した絵文字のID
    transaction_type = Column(String, default='react')
    effective_date = Column(DateTime, default=datetime.utcnow)

# 環境変数読み込みとBot設定
load_dotenv()
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# カスタム絵文字ポイント設定
EMOJI_POINTS = {
    '<:glucose_man:1360489607010975975>': 1,    # グルコースマン
    '<:saoringo:1378640284358938685>': 1,       # さおりんご
    '<:budouchan1:1379713964409225358>': 1,     # ブドウちゃん1
    '<:budouchan2:1379713967676723300>': 2,     # ブドウちゃん2
    '<:budouchan3:1379713977000394854>': 3,     # ブドウちゃん3
}

# データベースセッションの取得
async def get_db() -> AsyncGenerator[Session, None]:
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# ポイント付与処理
async def award_points(db: AsyncSession, recipient_id, giver_id, emoji_id, points):
    try:
        transaction = Transaction(
            recipient_id=recipient_id,
            points_awarded=points,
            giver_id=giver_id,
            emoji_id=emoji_id
        )
        db.add(transaction)
        await db.commit()
        return True
    except Exception as e:
        await db.rollback()
        print(f"❌ ポイント付与エラー: {e}")
        return False

# ポイント集計処理
async def calculate_points(db: AsyncSession, user_id=None, month=None):
    try:
        query = select(Transaction.recipient_id, Transaction.points_awarded)
        
        if user_id:
            query = query.filter(Transaction.recipient_id == user_id)
        
        if month:
            year, month = map(int, month.split('-'))
            first_day = datetime(year, month, 1)
            last_day = datetime(year, month, 1).replace(day=28) + timedelta(days=4)
            last_day = last_day - timedelta(days=last_day.day)
            query = query.filter(Transaction.effective_date >= first_day)
            query = query.filter(Transaction.effective_date <= last_day)
        
        results = await db.execute(query)
        results = results.all()
        
        points_dict = {}
        for recipient_id, points in results:
            points_dict[recipient_id] = points_dict.get(recipient_id, 0) + points
        
        return points_dict
    except Exception as e:
        print(f"❌ ポイント集計エラー: {e}")
        return {}

# ランキングメッセージ作成
async def format_ranking_message(points_dict, month=None, guild=None):
    try:
        ranking = sorted(points_dict.items(), key=lambda x: x[1], reverse=True)
        
        if not ranking:
            return "📊 ランキングデータがありません。"
        
        message = f"📊 {guild.name} {'月間' if month else '総合'}ランキング\n"
        for i, (user_id, points) in enumerate(ranking[:10]):
            user = guild.get_member(user_id)
            if user:
                message += f"{i + 1}. {user.display_name} {points}pt\n"
        
        return message
    except Exception as e:
        print(f"❌ ランキングメッセージ作成エラー: {e}")
        return "❌ ランキングの作成に失敗しました"

# リアクション追加イベント
@bot.event
async def on_raw_reaction_add(payload):
    try:
        emoji_str = str(payload.emoji)
        points = EMOJI_POINTS.get(emoji_str)
        
        if points:
            async with get_db() as db:
                await award_points(
                    db,
                    recipient_id=payload.message_id,
                    giver_id=payload.user_id,
                    emoji_id=str(payload.emoji),
                    points=points
                )
    except Exception as e:
        print(f"❌ リアクション処理エラー: {e}")

# ランキングコマンド
@bot.command(name="ランキング")
async def ranking(ctx):
    try:
        async with get_db() as db:
            points_dict = await calculate_points(db)
            message = await format_ranking_message(points_dict, guild=ctx.guild)
            await ctx.send(message)
    except Exception as e:
        print(f"❌ ランキングコマンドエラー: {e}")
        await ctx.send("❌ ランキングの表示に失敗しました")

# 月間ランキングコマンド
@bot.command(name="月間ランキング")
async def monthly_ranking(ctx, month: str = None):
    try:
        if month:
            try:
                year, month = map(int, month.split('-'))
            except:
                await ctx.send("⚠️ フォーマット: YYYY-MM")
                return
        
        async with get_db() as db:
            points_dict = await calculate_points(db, month=month)
            message = await format_ranking_message(points_dict, month=month, guild=ctx.guild)
            await ctx.send(message)
    except Exception as e:
        print(f"❌ 月間ランキングコマンドエラー: {e}")
        await ctx.send("❌ 月間ランキングの表示に失敗しました")

# ポイント表示コマンド
@bot.command(name="ポイント")
async def show_points(ctx):
    try:
        async with get_db() as db:
            points_dict = await calculate_points(db, user_id=ctx.author.id)
            total_points = points_dict.get(ctx.author.id, 0)
            await ctx.send(f"📊 {ctx.author.display_name} のポイント: {total_points}pt")
    except Exception as e:
        print(f"❌ ポイント表示コマンドエラー: {e}")
        await ctx.send("❌ ポイントの表示に失敗しました")

# デバッグ用のエラーハンドリング
@bot.event
async def on_command_error(ctx, error):
    print(f"❌ コマンドエラー: {error}")
    await ctx.send("⚠️ コマンドの実行中にエラーが発生しました")

# データベース初期化とBot起動
if __name__ == "__main__":
    try:
        # データベース初期化
        asyncio.run(init_db())
        
        # Bot起動
        bot.run(os.getenv("DISCORD_BOT_TOKEN"))
    except Exception as e:
        print(f"❌ Bot起動エラー: {e}")
