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
        
        # データベースの種類に応じたテーブル存在確認
        inspector = inspect(engine)
        
        # テーブルの存在確認
        if not inspector.has_table("transactions"):
            raise Exception("transactionsテーブルが作成されませんでした")
            
        print("✅ データベース初期化完了")
        
    except Exception as e:
        print(f"❌ データベース初期化エラー: {e}")
        import traceback
        traceback.print_exc()
        raise