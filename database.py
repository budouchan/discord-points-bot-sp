# database.py
from sqlalchemy import create_engine, inspect # inspectをインポート
from sqlalchemy.orm import sessionmaker
import os
from models import Base

# Railwayの環境変数を読み込む、なければローカルのSQLiteを使う
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./database.db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """
    データベースを初期化する
    """
    try:
        print("🚀 データベース初期化開始")
        
        # テーブルを（なければ）作成する
        # ※ drop_allは再起動のたびにデータが消えるので削除しました
        Base.metadata.create_all(bind=engine)
        
        # --- ここから修正 ---
        # SQLAlchemyのInspectorを使って、DBの種類を問わずテーブル情報を確認します
        inspector = inspect(engine)
        
        # テーブルの存在確認
        if not inspector.has_table("transactions"):
            raise Exception("transactionsテーブルが作成されませんでした")
        else:
            print("✅ transactionsテーブルの作成に成功")
            
        # カラム情報の確認
        columns = [column['name'] for column in inspector.get_columns("transactions")]
        print(f"✅ transactionsテーブルのカラム: {columns}")
        # --- ここまで修正 ---

        print("✅ データベース初期化完了")
        
    except Exception as e:
        print(f"❌ データベース初期化エラー: {e}")
        raise