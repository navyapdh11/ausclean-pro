import stripe
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class StripeService:
    def __init__(self):
        if settings.STRIPE_SECRET_KEY:
            stripe.api_key = settings.STRIPE_SECRET_KEY
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(stripe.error.RateLimitError),
        reraise=True,
    )
    async def create_payment_intent(
        self,
        amount: float,
        customer_email: str,
        metadata: dict | None = None,
    ) -> dict:
        """Create Stripe PaymentIntent with AUD currency."""
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Convert to cents
                currency="aud",
                customer_email=customer_email,
                metadata=metadata or {},
                automatic_payment_methods={"enabled": True},
                description=f"AusClean Pro - Cleaning Service Booking",
            )
            logger.info(f"PaymentIntent created: {intent.id} for ${amount:.2f} AUD")
            return {
                "id": intent.id,
                "client_secret": intent.client_secret,
                "status": intent.status,
            }
        except stripe.error.StripeError as e:
            logger.exception(f"Stripe error: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(stripe.error.RateLimitError),
        reraise=True,
    )
    async def create_checkout_session(
        self,
        amount: float,
        customer_email: str,
        success_url: str,
        cancel_url: str,
        metadata: dict | None = None,
        line_items: list | None = None,
    ) -> dict:
        """Create Stripe Checkout Session."""
        try:
            if line_items:
                items = line_items
            else:
                items = [{
                    "price_data": {
                        "currency": "aud",
                        "product_data": {
                            "name": "AusClean Pro - Cleaning Service",
                            "description": f"Booking total: ${amount:.2f} AUD (incl. GST)",
                        },
                        "unit_amount": int(amount * 100),
                    },
                    "quantity": 1,
                }]
            
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                mode="payment",
                customer_email=customer_email,
                line_items=items,
                success_url=success_url,
                cancel_url=cancel_url,
                metadata=metadata or {},
                billing_address_collection="required",
                automatic_tax={"enabled": True},
            )
            logger.info(f"Checkout session created: {session.id}")
            return {
                "id": session.id,
                "url": session.url,
            }
        except stripe.error.StripeError as e:
            logger.exception(f"Stripe checkout error: {e}")
            raise

stripe_service = StripeService()
