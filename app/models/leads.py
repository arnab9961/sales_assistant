from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from app.database import Base


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(50), unique=True, index=True, nullable=False)
    budget = Column(Float, nullable=False)
    interest = Column(String(255), nullable=False)
    message = Column(Text, nullable=True)

    # AI Qualification
    qualification_status = Column(String(50), default="Pending", index=True)  # Pending, Qualified, Needs manual review
    category = Column(String(20), nullable=True, index=True)  # Hot, Warm, Cold
    score = Column(Integer, nullable=True)  # 0 to 100
    reason = Column(Text, nullable=True)
    ai_error = Column(Text, nullable=True)
    n8n_status = Column(String(50), default="Not Sent")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CRMDealRecord(Base):
    __tablename__ = "crm_deal_records"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, nullable=True, index=True)
    customer_name = Column(String(255), nullable=True)
    region = Column(String(100), nullable=True)
    deal_value = Column(Float, nullable=True)
    lead_status = Column(String(50), nullable=True)
    raw_payload = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
