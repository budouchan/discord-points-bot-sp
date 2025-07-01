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
def calculate_points(db, user_id=None, month=None, year=None):
    try:
        query = select(Transaction.recipient_id, Transaction.points_awarded)
        
        if user_id:
            query = query.filter(Transaction.recipient_id == user_id)
        
        if year:
            first_day = datetime(year, 1, 1)
            last_day = datetime(year, 12, 31, 23, 59, 59)
            query = query.filter(Transaction.effective_date.between(first_day, last_day))
        elif month:
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
async def format_ranking_message(points_dict, guild):
    if not points_dict:
        return "ランキングデータがありません。"
    
    ranking = sorted(points_dict.items(), key=lambda x: x[1], reverse=True)
    
    message_body = ""
    print(f"🔍 ランキングリスト作成開始: {len(ranking)}件")

    for i, (user_id, points) in enumerate(ranking[:10]):
        display_name = f"ユーザーID: {user_id}"
        try:
            user = await guild.fetch_member(int(user_id))
            display_name = user.display_name
            print(f"✅ fetch_member成功: {display_name}")
        except discord.NotFound:
            print(f"⚠️ ユーザーがサーバーにいません: {user_id}")
            display_name = f"脱退したユーザー"
        except Exception as e:
            print(f"❌ ユーザー情報取得エラー: user_id={user_id}, error={e}")

        message_body += f"{i + 1}. {display_name} {points}pt\n"

    print(f"📋 最終リスト: {message_body.strip()}")
    return message_body

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
            ranking_body = await format_ranking_message(points_dict, ctx.guild)
            
            embed = discord.Embed(
                title=f"📊 {ctx.guild.name} 総合ランキング",
                description=ranking_body,
                color=discord.Color.purple()  # Botのアイコンに合わせた色
            )
            await ctx.send(embed=embed)
        finally:
            db.close()
    except Exception as e:
        print(f"❌ 総合ランキングエラー: {e}")
        import traceback
        traceback.print_exc()
        await ctx.send("❌ ランキングの作成に失敗しました")

# 月間ランキングコマンド（修正版）
@bot.command(name='月間ランキング')
async def monthly_ranking(ctx, month: str = None):
    """月間ランキングを表示します。"""
    try:
        # データベースからポイントを取得
        db = get_db()
        points = calculate_points(db, month=month)
        db.close()
        
        if not points:
            await ctx.send("📊 ランキングデータがありません。")
            return
            
        # ランキングの本文を作成
        ranking_body = await format_ranking_message(points, ctx.guild)
        
        # Embedを生成
        embed = discord.Embed(
            title=f"📊 {ctx.guild.name} 月間ランキング ({month if month else '今月'})",
            description=ranking_body,
            color=discord.Color.purple()  # Botのアイコンに合わせた色
        )
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        print(f"❌ 月間ランキングエラー: {e}")
        import traceback
        traceback.print_exc()
        await ctx.send("❌ ランキングの作成に失敗しました")

# ポイント表示コマンド（修正版）
@bot.command(name="ポイント")
async def command_show_points(ctx):
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

# 年間ランキングコマンド（新規追加）
@bot.command(name='年間ランキング')
async def yearly_ranking(ctx, year: int = None):
    """年間ランキングを表示します。年が指定されない場合は現在の年になります。"""
    try:
        if year is None:
            year = datetime.now().year

        db = get_db()
        points_dict = calculate_points(db, year=year)
        db.close()

        ranking_body = await format_ranking_message(points_dict, ctx.guild)
        
        # 年間MVP用にEmbedの色を金色にしてみます
        embed = discord.Embed(
            title=f"🏆 {ctx.guild.name} 年間ランキング ({year}年)",
            description=ranking_body,
            color=discord.Color.gold()
        )
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        print(f"❌ 年間ランキングエラー: {e}")
        import traceback
        traceback.print_exc()
        await ctx.send("❌ ランキングの作成に失敗しました")

# データベース初期化とBot起動
if __name__ == "__main__":
    try:
        # データベース初期化（同期関数なのでasyncio.runは不要）
        init_db()
        print("✅ データベース初期化完了")
        
        # Botの起動
        bot.run(os.getenv("DISCORD_BOT_TOKEN"))
    except Exception as e:
        print(f"❌ Bot起動エラー: {e}")
        import traceback
        traceback.print_exc()
