"""Seed script - creates initial data for AusClean Pro."""
from app.database import SessionLocal, engine, Base
from app.models import models
from app.auth import get_password_hash
from datetime import datetime, timedelta

def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        # Create service segments
        segments = [
            {"name": "Regular Clean", "description": "Standard home or office cleaning", "base_price": 89.0, "duration_minutes": 120, "gst_rate": 0.10},
            {"name": "Deep Clean", "description": "Thorough deep cleaning for all areas", "base_price": 179.0, "duration_minutes": 240, "gst_rate": 0.10},
            {"name": "End of Lease", "description": "Bond-back guaranteed end-of-lease clean", "base_price": 229.0, "duration_minutes": 300, "gst_rate": 0.10, "metadata": {"bond_back_guarantee": True}},
            {"name": "Carpet Clean", "description": "Steam carpet cleaning up to 3 rooms", "base_price": 149.0, "duration_minutes": 150, "gst_rate": 0.10},
            {"name": "Window Clean", "description": "Interior + exterior window cleaning", "base_price": 119.0, "duration_minutes": 90, "gst_rate": 0.10},
            {"name": "Strata/Common Area", "description": "Strata compliance + common area cleaning", "base_price": 199.0, "duration_minutes": 180, "gst_rate": 0.10, "metadata": {"compliance_check": True}},
            {"name": "NDIS Supported Living", "description": "NDIS-approved cleaning for SIL participants", "base_price": 129.0, "duration_minutes": 150, "gst_rate": 0.10, "metadata": {"ndis_approved": True}},
        ]
        
        for seg_data in segments:
            existing = db.query(models.Segment).filter(models.Segment.name == seg_data["name"]).first()
            if not existing:
                segment = models.Segment(**seg_data)
                db.add(segment)
        
        # Create demo user
        existing_user = db.query(models.User).filter(models.User.email == "demo@auscleanpro.com.au").first()
        if not existing_user:
            user = models.User(
                email="demo@auscleanpro.com.au",
                hashed_password=get_password_hash("demo12345"),
                full_name="Demo User",
                phone="0400 000 000",
                is_active=True,
                is_admin=True,
            )
            db.add(user)
        
        db.commit()
        print("✅ Database seeded successfully!")
        print(f"   - {len(segments)} service segments created")
        print("   - Demo user: demo@auscleanpro.com.au / demo12345")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Seeding failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed()
