import os
from sqlalchemy import create_engine, MetaData, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# 環境変数でDB種別を自動判定
DATABASE_URL = os.getenv('DATABASE_URL')

if DATABASE_URL and DATABASE_URL.startswith('postgresql://'):
    # 🐘 PostgreSQL (Railway)
    print("🐘 PostgreSQL接続モード")
    engine = create_engine(
        DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=False
    )
    DB_TYPE = 'postgresql'
else:
    # 📁 SQLite (ローカル)
    print("📁 SQLite接続モード")
    engine = create_engine(
        'sqlite:///points.db.backup',
        poolclass=StaticPool,
        connect_args={
            'check_same_thread': False,
            'timeout': 20
        },
        echo=False
    )
    DB_TYPE = 'sqlite'

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    """データベース初期化 - DB種別に応じた安全な処理"""
    try:
        print(f"🚀 データベース初期化開始 ({DB_TYPE})")
        
        # modelsをインポート
        import models
        
        if DB_TYPE == 'postgresql':
            # PostgreSQL: テーブル存在確認後に作成
            inspector = inspect(engine)
            existing_tables = inspector.get_table_names()
            
            if not existing_tables:
                print("📊 PostgreSQLテーブル作成中...")
                Base.metadata.create_all(bind=engine)
                print("✅ PostgreSQLテーブル作成完了")
            else:
                print(f"✅ PostgreSQLテーブル確認済み: {existing_tables}")
                # 既存テーブルがあっても、新しいテーブルがあれば作成
                Base.metadata.create_all(bind=engine)
                
        else:
            # SQLite: 通常の作成処理
            print("📊 SQLiteテーブル確認/作成中...")
            Base.metadata.create_all(bind=engine)
            print("✅ SQLiteテーブル準備完了")
            
        print("🎉 データベース初期化成功")
        
    except Exception as e:
        print(f"❌ データベース初期化エラー: {e}")
        print(f"🔍 DB種別: {DB_TYPE}")
        print(f"🔍 接続先: {DATABASE_URL if DATABASE_URL else 'SQLite'}")
        import traceback
        traceback.print_exc()
        raise

def get_db_info():
    """デバッグ用: DB接続情報取得"""
    return {
        'type': DB_TYPE,
        'url': DATABASE_URL if DATABASE_URL else 'sqlite:///points.db.backup',
        'engine': str(engine.url)
    }

def test_connection():
    """データベース接続テスト"""
    try:
        with SessionLocal() as session:
            # SQLAlchemyの警告を回避するためtext()を使用
            result = session.execute(text("SELECT 1"))
            result.fetchone()  # 結果を取得
            print(f"✅ {DB_TYPE} 接続テスト成功")
            return True
    except Exception as e:
        print(f"❌ {DB_TYPE} 接続テスト失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def get_db():
    """データベースセッションを取得（依存性注入用）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()