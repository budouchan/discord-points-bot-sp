from sqlalchemy import Column, Integer, String, DateTime, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Transaction(Base):
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True, index=True)
    recipient_id = Column(BigInteger, nullable=False)  # ポイントを受け取った人のID
    points_awarded = Column(Integer, nullable=False)   # 与えられたポイント数
    giver_id = Column(BigInteger)                     # ポイントを与えた人のID
    emoji_id = Column(String)                         # 使用した絵文字のID
    transaction_type = Column(String, default='react')
    effective_date = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Transaction(recipient={self.recipient_id}, points={self.points_awarded}, date={self.effective_date})>"
