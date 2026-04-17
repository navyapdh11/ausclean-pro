from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

# Users
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    phone: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserResponse(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# Segments
class SegmentBase(BaseModel):
    name: str
    description: Optional[str] = None
    base_price: float
    duration_minutes: int = 120

class SegmentCreate(SegmentBase):
    pass

class SegmentResponse(SegmentBase):
    id: int
    is_active: bool
    gst_rate: float
    
    class Config:
        from_attributes = True

# Bookings
class BookingCreate(BaseModel):
    segment_id: int
    service_type: str
    property_type: Optional[str] = None
    bedrooms: int = 1
    bathrooms: int = 1
    address: str
    suburb: str
    state: str = Field(..., pattern="^(NSW|VIC|QLD|SA|WA|TAS|NT|ACT)$")
    postcode: str
    booking_date: datetime
    ndis_number: Optional[str] = None
    ndis_plan_manager: Optional[str] = None
    strata_lot: Optional[str] = None
    strata_manager_contact: Optional[str] = None
    notes: Optional[str] = None

class BookingResponse(BaseModel):
    id: int
    user_id: Optional[int]
    service_type: str
    address: str
    suburb: str
    state: str
    postcode: str
    booking_date: datetime
    amount: float
    currency: str
    gst_included: float
    status: str
    ndis_number: Optional[str]
    stripe_payment_intent_id: Optional[str]
    xero_invoice_id: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

# Payments
class PaymentIntentRequest(BaseModel):
    amount: float
    customer_email: EmailStr
    booking_id: Optional[int] = None
    booking_metadata: Optional[Dict[str, Any]] = None

class PaymentIntentResponse(BaseModel):
    id: str
    client_secret: str
    status: str

# Auth
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# Reviews
class ReviewCreate(BaseModel):
    booking_id: int
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None

class ReviewResponse(BaseModel):
    id: int
    rating: int
    comment: Optional[str]
    sentiment_score: Optional[float]
    churn_probability: Optional[float]
    created_at: datetime
    
    class Config:
        from_attributes = True

# Compliance
class ComplianceResponse(BaseModel):
    state: str
    compliance_type: str
    is_compliant: bool
    portal_url: Optional[str] = None
    notes: Optional[str] = None

# Chat
class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    intent: Optional[str] = None
    booking_suggestion: Optional[Dict[str, Any]] = None
