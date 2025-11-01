
# backend/app/models/dataset.py
from sqlalchemy import Column, Integer, String, DateTime, JSON, Numeric, Index
from sqlalchemy.sql import func
from app.db.database import Base

class RawSnapshot(Base):
    __tablename__ = "raw_snapshots"
    id = Column(Integer, primary_key=True, index=True)
    dataset = Column(String(128), index=True)
    fetched_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    payload = Column(JSON)

class DistrictMonthly(Base):
    __tablename__ = "district_monthly"
    id = Column(Integer, primary_key=True, index=True)
    state_code = Column(String(32), index=True)
    state_name = Column(String(128), index=True)
    district_code = Column(String(64), index=True)
    district_name = Column(String(128), index=True)
    fin_year = Column(String(32), index=True)
    month = Column(String(32), index=True)
    total_households_worked = Column(Integer)
    total_individuals_worked = Column(Integer)
    persondays = Column(Integer)
    wages = Column(Numeric)
    avg_wage = Column(Numeric)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_district_time", "state_code", "district_code", "fin_year", "month"),
    )
