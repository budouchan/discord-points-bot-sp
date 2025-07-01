# database.py
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
import os
from models import Base

# Railwayの環境変数を読み込む、なければローカルのSQLiteを使う
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./database.db")

# PostgreSQLのURLが指定されている場合は、接続オプションを追加
if DATABASE_URL and DATABASE_URL.startswith('postgres'):
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """
    データベースを初期化する
    """
    try:
        print("🚀 データベース初期化開始")
        
        # テーブルを（なければ）作成する
        Base.metadata.create_all(bind=engine)
        
        # データベースの種類を確認
        is_postgres = DATABASE_URL and DATABASE_URL.startswith('postgres')
        
        # テーブル存在確認（データベースの種類に応じてクエリを変更）
        with engine.connect() as conn:
            if is_postgres:
                # PostgreSQL用のテーブル存在確認
                result = conn.execute(
                    """
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'transactions'
                    );
                    """
                )
                table_exists = result.scalar()
            else:
                # SQLite用のテーブル存在確認
                result = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='transactions'"
                )
                table_exists = result.fetchone() is not None
        
        if not table_exists:
            raise Exception("transactionsテーブルが作成されませんでした")
            
        print("✅ データベース初期化完了")
        
    except Exception as e:
        print(f"❌ データベース初期化エラー: {e}")
        import traceback
        traceback.print_exc()
        raise