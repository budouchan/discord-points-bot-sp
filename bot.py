import sys
import os
sys.path.insert(0, "/app")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import os
import asyncio
from datetime import datetime, timedelta
import discord
from discord.ext import commands
from dotenv import load_dotenv
from database import SessionLocal, init_db
from sqlalchemy import Column, Integer, BigInteger, String, DateTime, select
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Transaction(Base):
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True, index=True)
    recipient_id = Column(BigInteger, nullable=False)
    points_awarded = Column(Integer, nullable=False)
    giver_id = Column(BigInteger)
    emoji_id = Column(String)
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

# データベースセッションの取得（修正版）
def get_db():
    return SessionLocal()

# ポイント付与処理（修正版）
def award_points(db, recipient_id, giver_id, emoji_id, points):
    try:
        transaction = Transaction(
            recipient_id=recipient_id,
            points_awarded=points,
            giver_id=giver_id,
            emoji_id=emoji_id
        )
        db.add(transaction)
        db.commit()
        print(f"✅ ポイント付与成功: {recipient_id} に {points}pt")
        return True
    except Exception as e:
        db.rollback()
        print(f"❌ ポイント付与エラー: {e}")
        return False

# ポイント集計処理（修正版）
def calculate_points(db, user_id=None, month=None):
    try:
        query = select(Transaction.recipient_id, Transaction.points_awarded)
        
        if user_id:
            query = query.filter(Transaction.recipient_id == user_id)
        
        if month:
            # month が文字列の場合のみ split を実行
            if isinstance(month, str):
                year, month_num = map(int, month.split('-'))
                first_day = datetime(year, month_num, 1)
                last_day = datetime(year, month_num, 1).replace(day=28) + timedelta(days=4)
                last_day = last_day - timedelta(days=last_day.day)
                query = query.filter(Transaction.effective_date >= first_day)
                query = query.filter(Transaction.effective_date <= last_day)
        
        results = db.execute(query)
        results = results.all()
        
        points_dict = {}
        for recipient_id, points in results:
            points_dict[recipient_id] = points_dict.get(recipient_id, 0) + points
        
        print(f"📊 集計結果: {points_dict}")
        return points_dict
    except Exception as e:
        print(f"❌ ポイント集計エラー: {e}")
        return {}

# ランキングメッセージ作成（修正版）
def format_ranking_message(points_dict, month=None, guild=None):
    try:
        ranking = sorted(points_dict.items(), key=lambda x: x[1], reverse=True)
        
        if not ranking:
            return "📊 ランキングデータがありません。"
        
        message = f"📊 {guild.name} {'月間' if month else '総合'}ランキング\n"
        
        print(f"🔍 ランキング処理開始: {len(ranking)}件のデータ")
        
        for i, (user_id, points) in enumerate(ranking[:10]):
            try:
                print(f"🔍 処理中: user_id={user_id}, points={points}")
                
                # user_idを整数に変換
                user_id_int = int(user_id)
                
                # 複数の方法でユーザー名を取得
                user = guild.get_member(user_id_int)
                if user:
                    display_name = user.display_name
                    print(f"🔍 guild.get_member成功: {display_name}")
                else:
                    # get_memberで取得できない場合はbot.get_userを試す
                    user = bot.get_user(user_id_int)
                    if user:
                        display_name = user.display_name or user.name
                        print(f"🔍 bot.get_user成功: {display_name}")
                    else:
                        display_name = f"ユーザー{user_id}"
                        print(f"🔍 ユーザー名取得失敗、IDで表示: {display_name}")
                
                line = f"{i + 1}. {display_name} {points}pt\n"
                message += line
                print(f"🔍 ランキング行追加: {line.strip()}")
                
            except Exception as e:
                print(f"❌ ユーザー処理エラー: user_id={user_id}, error={e}")
                message += f"{i + 1}. ユーザー{user_id} {points}pt\n"
        
        print(f"📋 最終メッセージ: {message}")
        return message
        
    except Exception as e:
        print(f"❌ ランキングメッセージ作成エラー: {e}")
        import traceback
        traceback.print_exc()
        return "❌ ランキングの作成に失敗しました"

# リアクション削除イベント（新規追加）
@bot.event
async def on_raw_reaction_remove(payload):
    """リアクション削除時にポイントを減算"""
    try:
        # Botの反応は無視
        if payload.user_id == bot.user.id:
            return
            
        # メッセージを取得
        channel = bot.get_channel(payload.channel_id)
        if not channel:
            return
            
        message = await channel.fetch_message(payload.message_id)
        
        # メッセージ作成者とリアクションしたユーザーが同じ場合は無視
        if message.author.id == payload.user_id:
            return
            
        # ポイントの計算
        emoji_str = str(payload.emoji)
        points = EMOJI_POINTS.get(emoji_str)
        
        if points:
            db = get_db()
            try:
                # ポイントを減算
                transaction = Transaction(
                    recipient_id=message.author.id,
                    points_awarded=-points,  # マイナス値でポイントを減算
                    giver_id=payload.user_id,
                    emoji_id=str(payload.emoji),
                    transaction_type='react_remove'
                )
                db.add(transaction)
                db.commit()
                print(f"✅ ポイント減算成功: {message.author.display_name} から {-points}pt")
            finally:
                db.close()
    except Exception as e:
        print(f"❌ リアクション削除処理エラー: {e}")

# リアクション追加イベント（修正版）
@bot.event
async def on_raw_reaction_add(payload):
    try:
        # Botの反応は無視
        if payload.user_id == bot.user.id:
            return
            
        # メッセージ作成者を取得
        channel = bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        
        emoji_str = str(payload.emoji)
        points = EMOJI_POINTS.get(emoji_str)
        
        print(f"🎉 リアクション検出: {emoji_str}")
        
        if points and message.author.id != payload.user_id:  # 自分への反応を除外
            db = get_db()
            try:
                award_points(
                    db,
                    recipient_id=message.author.id,
                    giver_id=payload.user_id,
                    emoji_id=str(payload.emoji),
                    points=points
                )
                
                # ユーザー名取得を複数の方法で試す
                user = message.author  # メッセージ作成者から直接取得
                user_name = user.display_name if user else "未知のユーザー"
                
                # デバッグログ追加
                print(f"🔍 デバッグ: user={user}, user.display_name={user.display_name if user else 'None'}")
                
                print(f"✅ ポイント付与成功: {message.author.id} に {points}pt")
                print(f"🎉 {user_name} が {points}pt 獲得！")
                
            except Exception as e:
                print(f"❌ ポイント付与エラー: {e}")
            finally:
                db.close()
                
    except Exception as e:
        print(f"❌ リアクション処理エラー: {e}")

# ランキングコマンド（修正版）
@bot.command(name="ランキング")
async def ranking(ctx):
    try:
        db = get_db()
        try:
            points_dict = calculate_points(db)
            message = format_ranking_message(points_dict, guild=ctx.guild)
            await ctx.send(message)
        finally:
            db.close()
    except Exception as e:
        print(f"❌ ランキングコマンドエラー: {e}")
        await ctx.send("❌ ランキングの表示に失敗しました")

# 月間ランキングコマンド（修正版）
@bot.command(name="月間ランキング")
async def monthly_ranking(ctx, month: str = None):
    try:
        if month:
            try:
                year, month_num = map(int, month.split('-'))
            except:
                await ctx.send("⚠️ フォーマット: YYYY-MM")
                return
        
        db = get_db()
        try:
            points_dict = calculate_points(db, month=month)
            message = format_ranking_message(points_dict, month=month, guild=ctx.guild)
            await ctx.send(message)
        finally:
            db.close()
    except Exception as e:
        print(f"❌ 月間ランキングコマンドエラー: {e}")
        await ctx.send("❌ 月間ランキングの表示に失敗しました")

# ポイント表示コマンド（修正版）
@bot.command(name="ポイント")
async def show_points(ctx):
    try:
        db = get_db()
        try:
            points_dict = calculate_points(db, user_id=ctx.author.id)
            total_points = points_dict.get(ctx.author.id, 0)
            await ctx.send(f"📊 {ctx.author.display_name} のポイント: {total_points}pt")
        finally:
            db.close()
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
        # データベース初期化（同期関数なのでasyncio.runは不要）
        init_db()
        
        # Bot起動
        bot.run(os.getenv("DISCORD_BOT_TOKEN"))
    except Exception as e:
        print(f"❌ Bot起動エラー: {e}")