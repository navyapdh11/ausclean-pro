from sqlalchemy.orm import Session
from app.models import models
from app.auth import get_password_hash
from typing import Optional, List

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, email: str, password: str, full_name: Optional[str] = None):
    user = models.User(
        email=email,
        hashed_password=get_password_hash(password),
        full_name=full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_segments(db: Session, active_only: bool = True):
    query = db.query(models.Segment)
    if active_only:
        query = query.filter(models.Segment.is_active == True)
    return query.all()

def get_segment(db: Session, segment_id: int):
    return db.query(models.Segment).filter(models.Segment.id == segment_id).first()

def create_booking(db: Session, booking_data: dict):
    booking = models.Booking(**booking_data)
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking

def get_booking(db: Session, booking_id: int):
    return db.query(models.Booking).filter(models.Booking.id == booking_id).first()

def get_bookings_by_user(db: Session, user_id: int) -> List[models.Booking]:
    return db.query(models.Booking).filter(models.Booking.user_id == user_id).order_by(models.Booking.created_at.desc()).all()

def update_booking_status(db: Session, booking_id: int, status: str, **kwargs):
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if booking:
        booking.status = status
        for key, value in kwargs.items():
            if hasattr(booking, key):
                setattr(booking, key, value)
        db.commit()
        db.refresh(booking)
    return booking

def create_review(db: Session, review_data: dict):
    review = models.Review(**review_data)
    db.add(review)
    db.commit()
    db.refresh(review)
    return review

def get_reviews_by_user(db: Session, user_id: int) -> List[models.Review]:
    return db.query(models.Review).filter(models.Review.user_id == user_id).all()

def create_compliance_check(db: Session, check_data: dict):
    check = models.ComplianceCheck(**check_data)
    db.add(check)
    db.commit()
    db.refresh(check)
    return check
