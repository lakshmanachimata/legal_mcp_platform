#!/usr/bin/env python3
"""
Database setup script for Legal AI Case Management System
Creates database, tables, and sample data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import date
from app.models import Base, Case, Party, TimelineEvent, FinancialRecord

def create_database():
    """Create the legal_db database if it doesn't exist"""
    # Connect to default postgres database
    engine = create_engine("postgresql://lakshmana@localhost:5432/postgres")
    
    with engine.connect() as conn:
        # Set autocommit to True to avoid transaction block issues
        conn.execute(text("COMMIT"))
        
        # Check if database exists
        result = conn.execute(text("SELECT 1 FROM pg_database WHERE datname = 'legal_db'"))
        if not result.fetchone():
            # Create database
            conn.execute(text("CREATE DATABASE legal_db"))
            print("✅ Created legal_db database")
        else:
            print("✅ legal_db database already exists")
    
    engine.dispose()

def create_tables():
    """Create all tables"""
    from app.db import engine
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✅ Created all tables")

def insert_sample_data():
    """Insert sample case data"""
    from app.db import SessionLocal
    
    db = SessionLocal()
    
    try:
        # Check which cases already exist
        existing_case_ids = [case.case_id for case in db.query(Case).filter(Case.case_id.in_(["2024-PI-001", "2024-PI-002", "2024-PI-003"])).all()]
        missing_cases = []
        
        # Define all cases
        all_cases = [
            Case(
                case_id="2024-PI-001",
                case_type="Personal Injury",
                date_filed=date(2024, 1, 15),
                status="Active",
                attorney_id=1,
                case_summary="Motor vehicle accident case involving rear-end collision"
            ),
            Case(
                case_id="2024-PI-002",
                case_type="Medical Malpractice",
                date_filed=date(2024, 2, 20),
                status="Active",
                attorney_id=1,
                case_summary="Surgical error case involving improper procedure"
            ),
            Case(
                case_id="2024-PI-003",
                case_type="Slip and Fall",
                date_filed=date(2024, 3, 10),
                status="Active",
                attorney_id=1,
                case_summary="Premises liability case involving wet floor injury"
            )
        ]
        
        # Add only missing cases
        for case in all_cases:
            if case.case_id not in existing_case_ids:
                missing_cases.append(case)
        
        if missing_cases:
            db.add_all(missing_cases)
            print(f"✅ Added {len(missing_cases)} new cases")
        else:
            print("✅ All sample cases already exist")
            return
        
        # Create parties for missing cases only
        parties = []
        for case_id in ["2024-PI-001", "2024-PI-002", "2024-PI-003"]:
            if case_id not in existing_case_ids:
                if case_id == "2024-PI-001":
                    parties.extend([
                        Party(
                            case_id="2024-PI-001",
                            party_type="plaintiff",
                            name="John Smith",
                            contact_info="555-0101"
                        ),
                        Party(
                            case_id="2024-PI-001",
                            party_type="defendant",
                            name="ABC Insurance Company",
                            contact_info="555-0202"
                        )
                    ])
                elif case_id == "2024-PI-002":
                    parties.extend([
                        Party(
                            case_id="2024-PI-002",
                            party_type="plaintiff",
                            name="Sarah Johnson",
                            contact_info="555-0303"
                        ),
                        Party(
                            case_id="2024-PI-002",
                            party_type="defendant",
                            name="City General Hospital",
                            contact_info="555-0404"
                        )
                    ])
                elif case_id == "2024-PI-003":
                    parties.extend([
                        Party(
                            case_id="2024-PI-003",
                            party_type="plaintiff",
                            name="Michael Brown",
                            contact_info="555-0505"
                        ),
                        Party(
                            case_id="2024-PI-003",
                            party_type="defendant",
                            name="Mall Management LLC",
                            contact_info="555-0606"
                        )
                    ])
        
        if parties:
            db.add_all(parties)
        
        # Create timeline events for missing cases only
        events = []
        for case_id in ["2024-PI-001", "2024-PI-002", "2024-PI-003"]:
            if case_id not in existing_case_ids:
                if case_id == "2024-PI-001":
                    events.extend([
                        TimelineEvent(
                            case_id="2024-PI-001",
                            event_date=date(2024, 1, 10),
                            description="Motor vehicle accident occurred"
                        ),
                        TimelineEvent(
                            case_id="2024-PI-001",
                            event_date=date(2024, 1, 15),
                            description="Case filed with court"
                        ),
                        TimelineEvent(
                            case_id="2024-PI-001",
                            event_date=date(2024, 2, 1),
                            description="Initial discovery served"
                        )
                    ])
                elif case_id == "2024-PI-002":
                    events.extend([
                        TimelineEvent(
                            case_id="2024-PI-002",
                            event_date=date(2024, 2, 15),
                            description="Surgical procedure performed"
                        ),
                        TimelineEvent(
                            case_id="2024-PI-002",
                            event_date=date(2024, 2, 20),
                            description="Case filed with court"
                        ),
                        TimelineEvent(
                            case_id="2024-PI-002",
                            event_date=date(2024, 3, 5),
                            description="Medical records subpoenaed"
                        )
                    ])
                elif case_id == "2024-PI-003":
                    events.extend([
                        TimelineEvent(
                            case_id="2024-PI-003",
                            event_date=date(2024, 3, 5),
                            description="Slip and fall accident occurred"
                        ),
                        TimelineEvent(
                            case_id="2024-PI-003",
                            event_date=date(2024, 3, 10),
                            description="Case filed with court"
                        ),
                        TimelineEvent(
                            case_id="2024-PI-003",
                            event_date=date(2024, 3, 25),
                            description="Site inspection completed"
                        )
                    ])
        
        if events:
            db.add_all(events)
        
        # Create financial records for missing cases only
        financials = []
        for case_id in ["2024-PI-001", "2024-PI-002", "2024-PI-003"]:
            if case_id not in existing_case_ids:
                if case_id == "2024-PI-001":
                    financials.extend([
                        FinancialRecord(
                            case_id="2024-PI-001",
                            record_type="medical",
                            amount=15000,
                            description="Emergency room and follow-up treatment"
                        ),
                        FinancialRecord(
                            case_id="2024-PI-001",
                            record_type="medical",
                            amount=5000,
                            description="Physical therapy sessions"
                        ),
                        FinancialRecord(
                            case_id="2024-PI-001",
                            record_type="lost_wages",
                            amount=8000,
                            description="Lost wages due to injury"
                        ),
                        FinancialRecord(
                            case_id="2024-PI-001",
                            record_type="pain_suffering",
                            amount=25000,
                            description="Pain and suffering damages"
                        )
                    ])
                elif case_id == "2024-PI-002":
                    financials.extend([
                        FinancialRecord(
                            case_id="2024-PI-002",
                            record_type="medical",
                            amount=45000,
                            description="Corrective surgery required"
                        ),
                        FinancialRecord(
                            case_id="2024-PI-002",
                            record_type="medical",
                            amount=12000,
                            description="Rehabilitation therapy"
                        ),
                        FinancialRecord(
                            case_id="2024-PI-002",
                            record_type="lost_wages",
                            amount=15000,
                            description="Lost wages due to medical complications"
                        ),
                        FinancialRecord(
                            case_id="2024-PI-002",
                            record_type="pain_suffering",
                            amount=75000,
                            description="Pain and suffering damages"
                        )
                    ])
                elif case_id == "2024-PI-003":
                    financials.extend([
                        FinancialRecord(
                            case_id="2024-PI-003",
                            record_type="medical",
                            amount=8000,
                            description="Emergency room treatment"
                        ),
                        FinancialRecord(
                            case_id="2024-PI-003",
                            record_type="medical",
                            amount=3000,
                            description="Physical therapy"
                        ),
                        FinancialRecord(
                            case_id="2024-PI-003",
                            record_type="lost_wages",
                            amount=5000,
                            description="Lost wages due to injury"
                        ),
                        FinancialRecord(
                            case_id="2024-PI-003",
                            record_type="pain_suffering",
                            amount=15000,
                            description="Pain and suffering damages"
                        )
                    ])
        
        if financials:
            db.add_all(financials)
        
        db.commit()
        print("✅ Inserted sample data for cases 2024-PI-001, 2024-PI-002, and 2024-PI-003")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error inserting sample data: {e}")
        raise
    finally:
        db.close()

def main():
    """Main setup function"""
    print("🚀 Setting up Legal AI Case Management Database")
    print("=" * 50)
    
    try:
        create_database()
        create_tables()
        insert_sample_data()
        
        print("\n✅ Database setup complete!")
        print("You can now run the application with:")
        print("python -m uvicorn app.main:app --reload")
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 