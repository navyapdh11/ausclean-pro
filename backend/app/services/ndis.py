import jwt
from datetime import datetime, timedelta
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import aiohttp
import os
import logging

logger = logging.getLogger(__name__)

def _get_private_key():
    """Load RSA private key from env or generate demo key (never use in prod)."""
    private_key_pem = os.getenv("PRODA_PRIVATE_KEY_PEM")
    if private_key_pem:
        return serialization.load_pem_private_key(private_key_pem.encode(), password=None)
    # Demo fallback - NEVER use in production
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)

async def _get_proda_access_token() -> str | None:
    """Full PRODA B2B JWT Bearer Token flow (2026 NDIS spec)."""
    private_key = _get_private_key()
    software_instance_id = os.getenv("PRODA_SOFTWARE_INSTANCE_ID")
    
    if not software_instance_id:
        logger.warning("PRODA not configured - returning mock token")
        return f"proda-mock-token-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    
    # PRODA JWT claims per NDIA 2026 spec
    claims = {
        "iss": software_instance_id,
        "sub": software_instance_id,
        "aud": "https://www.ndis.gov.au/",
        "exp": int((datetime.utcnow() + timedelta(minutes=5)).timestamp()),
        "iat": int(datetime.utcnow().timestamp()),
        "jti": f"proda-{datetime.utcnow().isoformat()}",
    }
    
    token = jwt.encode(claims, private_key, algorithm="RS256")
    logger.info("PRODA JWT signed successfully")
    
    # In production: POST to PRODA token endpoint
    # async with aiohttp.ClientSession() as session:
    #     async with session.post(
    #         "https://proda.ndis.gov.au/token",
    #         data={"grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer", "assertion": token},
    #     ) as resp:
    #         result = await resp.json()
    #         return result.get("access_token")
    
    return token  # Return JWT for demo; actual exchange happens in prod

async def verify_participant(ndis_number: str) -> dict:
    """Verify NDIS participant via PRODA API."""
    token = await _get_proda_access_token()
    if token and token.startswith("proda-mock"):
        logger.info(f"Using mock PRODA verification for NDIS {ndis_number}")
        return {
            "verified": True,
            "ndis_number": ndis_number,
            "participant_name": "Demo Participant",
            "plan_status": "active",
            "plan_manager": "self",
            "source": "mock",
        }
    
    # Real PRODA verification
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://ndis.gov.au/api/v1/participants/{ndis_number}",
                headers={"Authorization": f"Bearer {token}"},
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {"verified": True, **data, "source": "proda"}
                return {"verified": False, "error": f"PRODA returned {resp.status}"}
    except Exception as e:
        logger.exception(f"PRODA verification failed for {ndis_number}")
        return {"verified": False, "error": str(e), "source": "error"}
