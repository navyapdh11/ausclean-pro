import logging
import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class XeroService:
    """Xero accounting integration for invoice creation."""
    
    def __init__(self):
        self.base_url = "https://api.xero.com/api.xro/2.0"
        self.access_token = settings.XERO_ACCESS_TOKEN
        self.tenant_id = settings.XERO_TENANT_ID
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=15),
        retry=retry_if_exception_type(aiohttp.ClientError),
        reraise=True,
    )
    async def create_invoice(self, booking) -> dict | None:
        """Create Xero invoice for confirmed booking (fire-and-forget)."""
        if not self.access_token or self.access_token == "dummy":
            logger.info("Xero not configured - skipping invoice creation")
            return None
        
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Xero-tenant-id": self.tenant_id,
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
            
            gst_amount = booking.amount * 0.1  # 10% Australian GST
            total_with_gst = booking.amount + gst_amount
            
            invoice_data = {
                "Type": "ACCREC",
                "Contact": {
                    "Name": booking.user.full_name or booking.user.email if booking.user else "Customer",
                    "EmailAddress": booking.user.email if booking.user else "",
                },
                "LineItems": [{
                    "Description": f"Cleaning Service - {booking.service_type}",
                    "Quantity": 1,
                    "UnitAmount": round(booking.amount, 2),
                    "AccountCode": "200",  # Sales account
                    "TaxType": "OUTPUT",
                }],
                "Reference": f"BOOKING-{booking.id}",
                "InvoiceNumber": f"AC-{booking.id:06d}",
                "DueDate": (booking.booking_date.date()).isoformat(),
                "Status": "SUBMITTED",
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/Invoices",
                    headers=headers,
                    json=invoice_data,
                ) as resp:
                    if resp.status in (200, 201):
                        result = await resp.json()
                        invoice_id = result["Invoices"][0]["InvoiceID"]
                        logger.info(f"Xero invoice created: {invoice_id} for booking {booking.id}")
                        return {"invoice_id": invoice_id, "status": "created"}
                    else:
                        error_body = await resp.text()
                        logger.error(f"Xero API error {resp.status}: {error_body}")
                        return None
        except Exception as e:
            logger.exception(f"Failed to create Xero invoice for booking {booking.id}")
            return None

xero_service = XeroService()
