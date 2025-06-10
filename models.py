# models.py

from sqlalchemy import Column, Integer, String, DateTime, BigInteger
from database import Base # ドットなし
import datetime

class Transaction(Base):
    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True, index=True)
    recipient_id = Column(BigInteger, nullable=False)
    points_awarded = Column(Integer, nullable=False)
    giver_id = Column(BigInteger)
    emoji_id = Column(String)
    transaction_type = Column(String, default='react')
    effective_date = Column(DateTime, default=datetime.datetime.utcnow)