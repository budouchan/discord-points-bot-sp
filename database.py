# database.py
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from models import Base, Transaction

# Railwayの環境変数を読み込む、なければローカルのSQLiteを使う
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./database.db")

# 同期エンジンを使用（非同期を削除）
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """
    データベースを初期化する
    """
    # ここでモデルをインポートすることが重要
    import models
    
    try:
        print("🚀 データベース初期化開始")
        
        # 既存のテーブルをすべて削除し、新しいテーブルを再作成する
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        
        # テーブルが正しく作成されたか確認
        with engine.connect() as conn:
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='transactions'"))
            if not result.fetchone():
                raise Exception("transactionsテーブルが作成されませんでした")
            else:
                print("✅ transactionsテーブルの作成に成功")
                
            # 作成されたテーブルの構造（カラム）を確認のため表示
            result = conn.execute(text("PRAGMA table_info(transactions)"))
            columns = [row[1] for row in result.fetchall()] # row[1] is the column name
            print(f"✅ transactionsテーブルのカラム: {columns}")
        print("✅ データベース初期化完了")
        
    except Exception as e:
        print(f"❌ データベース初期化エラー: {e}")
        raise