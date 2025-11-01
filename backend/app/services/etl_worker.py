# backend/app/services/etl_worker.py
import logging
from app.services.data_fetcher import fetch_dataset
from app.db.database import SessionLocal, engine
from app.models.dataset import Base, RawSnapshot, DistrictMonthly
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger("etl")
logger.setLevel(logging.INFO)

Base.metadata.create_all(bind=engine)

def _safe_int(v): 
    try: return int(v)
    except: return None

def _safe_float(v): 
    try: return float(v)
    except: return None

def upsert_from_record(session, rec):
    state_code = rec.get("state_code") or rec.get("state") or ""
    state_name = rec.get("state_name") or rec.get("state") or ""
    district_code = rec.get("district_code") or rec.get("district") or ""
    district_name = rec.get("district_name") or rec.get("district") or ""
    fin_year = rec.get("fin_year") or rec.get("financial_year") or ""
    month = rec.get("month") or ""

    total_households = _safe_int(rec.get("Total_Households_Worked") or rec.get("total_households_worked"))
    total_individuals = _safe_int(rec.get("Total_Individuals_Worked") or rec.get("total_individuals_worked"))
    persondays = _safe_int(rec.get("Persondays_of_Central_Liability_so_far") or rec.get("persondays"))
    wages = _safe_float(rec.get("Wages") or rec.get("wages"))
    avg_wage = _safe_float(rec.get("Average_Wage_rate_per_day_per_person") or rec.get("avg_wage"))

    session.query(DistrictMonthly).filter_by(
        state_code=state_code,
        district_code=district_code,
        fin_year=fin_year,
        month=month,
    ).delete()

    session.add(DistrictMonthly(
        state_code=state_code,
        state_name=state_name,
        district_code=district_code,
        district_name=district_name,
        fin_year=fin_year,
        month=month,
        total_households_worked=total_households,
        total_individuals_worked=total_individuals,
        persondays=persondays,
        wages=wages,
        avg_wage=avg_wage,
    ))

def run_etl_once(limit=5000):
    logger.info("🚀 Starting ETL fetch")
    records = fetch_dataset(limit=limit)
    if not records:
        logger.warning("⚠️ No records fetched from API.")
        return

    logger.info(f"✅ Fetched {len(records)} records")
    session = SessionLocal()
    try:
        session.add(RawSnapshot(dataset="mgnrega", payload={"records": records}))
        session.flush()

        for rec in records:
            try:
                upsert_from_record(session, rec)
            except Exception:
                logger.exception("Failed to upsert record")

        session.commit()
        logger.info(f"✅ ETL complete: {len(records)} records processed")
    except SQLAlchemyError:
        session.rollback()
        logger.exception("DB error during ETL")
    finally:
        session.close()

if __name__ == "__main__":
    run_etl_once()
