from fastapi import APIRouter, Depends, HTTPException, Request, Response, BackgroundTasks
from sqlalchemy.orm import Session
from app import crud, schemas
from app.database import get_db
from app.auth import authenticate_user, create_access_token, set_token_cookie
from app.ai.graph import graph
from app.ai.rag import get_rag_chain
from app.services import stripe as stripe_svc, xero as xero_svc, ndis as ndis_svc, strata as strata_svc, redis as redis_svc
from app.config import get_settings
from datetime import datetime
import asyncio
import logging
import stripe

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter()

# ============================================================================
# SEGMENTS
# ============================================================================
@router.get("/segments", response_model=list[schemas.SegmentResponse])
def list_segments(db: Session = Depends(get_db)):
    return crud.get_segments(db)

@router.get("/segments/{segment_id}", response_model=schemas.SegmentResponse)
def get_segment(segment_id: int, db: Session = Depends(get_db)):
    segment = crud.get_segment(db, segment_id)
    if not segment:
        raise HTTPException(404, "Segment not found")
    return segment

# ============================================================================
# BOOKINGS
# ============================================================================
@router.post("/bookings", response_model=schemas.BookingResponse)
async def create_booking(
    payload: schemas.BookingCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Create a new booking."""
    segment = crud.get_segment(db, payload.segment_id)
    if not segment:
        raise HTTPException(404, "Service segment not found")
    
    booking_data = {
        **payload.model_dump(),
        "amount": segment.base_price,
        "gst_included": segment.base_price * segment.gst_rate,
        "currency": "AUD",
        "duration_minutes": segment.duration_minutes,
    }
    
    booking = crud.create_booking(db, booking_data)
    logger.info(f"Booking created: {booking.id} - {payload.service_type}")
    
    # NDIS verification (background)
    if payload.ndis_number:
        background_tasks.add_task(ndis_svc.verify_participant, payload.ndis_number)
    
    # Strata compliance check (background)
    background_tasks.add_task(strata_svc.check_compliance, payload.state, payload.address)
    
    return booking

@router.get("/bookings/{booking_id}", response_model=schemas.BookingResponse)
def get_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = crud.get_booking(db, booking_id)
    if not booking:
        raise HTTPException(404, "Booking not found")
    return booking

# ============================================================================
# AUTH
# ============================================================================
@router.post("/auth/token", response_model=schemas.Token)
async def login(
    email: str,
    password: str,
    db: Session = Depends(get_db),
):
    user = crud.get_user_by_email(db, email)
    if not user or not crud.verify_password(password, user.hashed_password):
        raise HTTPException(401, "Invalid credentials")
    
    token = create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}

# ============================================================================
# CHAT (AI Agent)
# ============================================================================
@router.post("/chat", response_model=schemas.ChatResponse)
async def chat(payload: schemas.ChatRequest):
    """AI agent chat endpoint using LangGraph + RAG."""
    try:
        rag_chain = get_rag_chain()
        response = rag_chain.invoke({"question": payload.message})
        
        # Determine intent for analytics
        intent = None
        msg_lower = payload.message.lower()
        if any(w in msg_lower for w in ["book", "schedule", "appointment"]):
            intent = "booking"
        elif any(w in msg_lower for w in ["price", "cost", "how much"]):
            intent = "pricing"
        elif any(w in msg_lower for w in ["ndis"]):
            intent = "ndis"
        
        return schemas.ChatResponse(response=response, intent=intent)
    except Exception as e:
        logger.exception("Chat error")
        raise HTTPException(500, "AI service unavailable")

# ============================================================================
# PAYMENTS (Stripe)
# ============================================================================
@router.post("/payments/create-intent", response_model=schemas.PaymentIntentResponse)
async def create_payment_intent(payload: schemas.PaymentIntentRequest):
    """Create Stripe PaymentIntent for booking payment."""
    try:
        intent = await stripe_svc.stripe_service.create_payment_intent(
            amount=payload.amount,
            customer_email=payload.customer_email,
            metadata={"booking_id": str(payload.booking_id)} if payload.booking_id else {},
        )
        return schemas.PaymentIntentResponse(**intent)
    except Exception as e:
        logger.exception("Payment intent creation failed")
        raise HTTPException(400, "Payment intent failed")

@router.post("/payments/webhook")
async def stripe_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Stripe webhook - idempotent, signature-verified.
    
    On payment success: confirm booking → fire Xero invoice → NDIS verify → strata check.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except Exception as e:
        logger.error(f"Webhook signature verification failed: {e}")
        raise HTTPException(400, "Invalid signature")
    
    # Idempotency - ignore duplicate events
    event_id = event["id"]
    if await redis_svc.redis_client.get(f"stripe:event:{event_id}"):
        return {"status": "already_processed"}
    
    await redis_svc.redis_client.set(f"stripe:event:{event_id}", "processed", ex=86400)
    
    if event["type"] == "payment_intent.succeeded":
        intent = event["data"]["object"]
        metadata = intent.get("metadata", {})
        booking_id = metadata.get("booking_id")
        
        if booking_id:
            booking = crud.get_booking(db, int(booking_id))
            if booking:
                # Confirm booking
                crud.update_booking_status(
                    db, booking.id, "confirmed",
                    stripe_payment_intent_id=intent["id"],
                    stripe_event_id=event_id,
                )
                logger.info(f"Booking {booking.id} confirmed via Stripe webhook")
                
                # Parallel fan-out (fire-and-forget with retries)
                background_tasks.add_task(xero_svc.xero_service.create_invoice, booking)
                
                if booking.ndis_number:
                    background_tasks.add_task(ndis_svc.verify_participant, booking.ndis_number)
                
                background_tasks.add_task(
                    strata_svc.check_compliance, booking.state, booking.address
                )
                
                # Trigger Inngest event for workflow
                # inngest_client.send_sync(Event(name="booking.confirmed", data={"booking_id": booking.id}))
    
    return {"status": "success"}

# ============================================================================
# REVIEWS + CHURN
# ============================================================================
@router.post("/reviews", response_model=schemas.ReviewResponse)
async def create_review(payload: schemas.ReviewCreate, db: Session = Depends(get_db)):
    booking = crud.get_booking(db, payload.booking_id)
    if not booking:
        raise HTTPException(404, "Booking not found")
    
    review_data = {
        "user_id": booking.user_id,
        "booking_id": payload.booking_id,
        "rating": payload.rating,
        "comment": payload.comment,
        "sentiment_score": 0.0,  # Would be computed by sentiment analysis
        "churn_probability": 0.0,  # Computed by churn prediction
    }
    
    review = crud.create_review(db, review_data)
    return review

# ============================================================================
# NDIS
# ============================================================================
@router.get("/ndis/status/{ndis_number}")
async def ndis_status(ndis_number: str):
    """Check NDIS participant status via PRODA."""
    result = await ndis_svc.verify_participant(ndis_number)
    return result

# ============================================================================
# STRATA / STATE COMPLIANCE
# ============================================================================
@router.get("/strata/compliance/{state}", response_model=schemas.ComplianceResponse)
async def strata_compliance(state: str, address: str | None = None):
    """State/strata compliance check with portal links."""
    result = await strata_svc.check_compliance(state, address)
    return schemas.ComplianceResponse(
        state=result.get("state", state),
        compliance_type="strata",
        is_compliant=result.get("compliant", False),
        portal_url=result.get("portal", {}).get("url"),
        notes=result.get("notes"),
    )

# ============================================================================
# WEATHER / TRAFFIC (placeholder for cleaner scheduling)
# ============================================================================
@router.get("/weather/{suburb}")
async def weather(suburb: str):
    """Get weather for cleaner scheduling (placeholder)."""
    return {"suburb": suburb, "condition": "clear", "temperature": 22, "unit": "celsius"}

@router.get("/traffic/{suburb}")
async def traffic(suburb: str):
    """Get traffic conditions for cleaner travel time (placeholder)."""
    return {"suburb": suburb, "congestion": "low", "delay_minutes": 5}
