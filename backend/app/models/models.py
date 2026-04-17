from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    phone = Column(String(50))
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    bookings = relationship("Booking", back_populates="user")
    reviews = relationship("Review", back_populates="user")

class Booking(Base):
    __tablename__ = "bookings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    segment_id = Column(Integer, ForeignKey("segments.id"))
    
    # Service details
    service_type = Column(String(100), nullable=False)  # regular, deep, end-of-lease, carpet, window
    property_type = Column(String(50))  # residential, commercial, strata
    bedrooms = Column(Integer, default=1)
    bathrooms = Column(Integer, default=1)
    
    # Address
    address = Column(Text, nullable=False)
    suburb = Column(String(100), nullable=False)
    state = Column(String(3), nullable=False)  # NSW, VIC, QLD, etc.
    postcode = Column(String(4), nullable=False)
    
    # Scheduling
    booking_date = Column(DateTime(timezone=True), nullable=False)
    duration_minutes = Column(Integer, default=120)
    
    # Pricing
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="AUD")
    gst_included = Column(Float, default=0)
    
    # Status
    status = Column(String(50), default="pending")  # pending, confirmed, in-progress, completed, cancelled, no-show
    
    # NDIS
    ndis_number = Column(String(50))
    ndis_plan_manager = Column(String(50))  # self, plan-managed, ndia-managed
    
    # Strata
    strata_lot = Column(String(50))
    strata_manager_contact = Column(String(255))
    
    # Payment
    stripe_payment_intent_id = Column(String(255))
    stripe_event_id = Column(String(255))
    xero_invoice_id = Column(String(255))
    
    # Metadata
    notes = Column(Text)
    metadata = Column(JSON, default=dict)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    user = relationship("User", back_populates="bookings")
    segment = relationship("Segment", back_populates="bookings")

class Segment(Base):
    __tablename__ = "segments"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)  # End of Lease, Regular, Deep Clean, Carpet, Window, Strata
    description = Column(Text)
    base_price = Column(Float, nullable=False)
    gst_rate = Column(Float, default=0.10)  # 10% GST Australia
    duration_minutes = Column(Integer, default=120)
    is_active = Column(Boolean, default=True)
    metadata = Column(JSON, default=dict)
    
    bookings = relationship("Booking", back_populates="segment")

class Review(Base):
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    booking_id = Column(Integer, ForeignKey("bookings.id"))
    
    rating = Column(Integer, nullable=False)  # 1-5
    comment = Column(Text)
    sentiment_score = Column(Float)  # -1 to 1
    churn_probability = Column(Float)  # 0 to 1
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="reviews")

class ComplianceCheck(Base):
    __tablename__ = "compliance_checks"
    
    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"))
    state = Column(String(3), nullable=False)
    compliance_type = Column(String(50))  # strata, fair-trading, rtba, whs
    is_compliant = Column(Boolean, default=True)
    details = Column(JSON, default=dict)
    notes = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
