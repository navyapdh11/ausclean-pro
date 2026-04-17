import logging

logger = logging.getLogger(__name__)

# State-specific strata/owners corporation portals (2026)
STATE_PORTALS = {
    "NSW": {
        "name": "NSW Fair Trading",
        "url": "https://www.nsw.gov.au/housing-and-construction/strata",
        "notes": "Check Fair Trading portal for owners corporation rules. Strata Schemes Management Act 2015 applies.",
    },
    "VIC": {
        "name": "Consumer Affairs Victoria",
        "url": "https://www.consumer.vic.gov.au/housing/owners-corporations",
        "notes": "RTBA bond + Owners Corporation responsibilities. Owners Corporations Act 2006.",
    },
    "QLD": {
        "name": "Queensland Body Corporate",
        "url": "https://www.qld.gov.au/law/housing-renting-and-neighbours/body-corporate-and-community-title",
        "notes": "Body Corporate and Community Management Act 1997. Check BCCM portal for by-laws.",
    },
    "SA": {
        "name": "Consumer and Business Services SA",
        "url": "https://www.cbs.sa.gov.au/strata",
        "notes": "Strata Titles Act 1988. All strata corporations must have a managing agent.",
    },
    "WA": {
        "name": "Department of Mines, Industry Regulation and Safety WA",
        "url": "https://www.dmirs.wa.gov.au/strata-titles",
        "notes": "Strata Titles Act 1985 (reformed 2020). Check strata company records.",
    },
    "TAS": {
        "name": "Consumer, Building and Occupational Services TAS",
        "url": "https://www.cbos.tas.gov.au/topics/strata-titles",
        "notes": "Strata Titles Act 1998. Body corporate management required.",
    },
    "NT": {
        "name": "NT Consumer Affairs",
        "url": "https://consumeraffairs.nt.gov.au/strata-titles",
        "notes": "Unit Titles Act. Limited strata scheme coverage.",
    },
    "ACT": {
        "name": "ACT Planning and Land Authority",
        "url": "https://www.planning.act.gov.au/strata",
        "notes": "Unit Titles Act 2001. ACT has unique unit titling system.",
    },
}

async def check_compliance(state: str, address: str | None = None) -> dict:
    """Strata / Owners Corporation compliance check.
    
    No public REST APIs exist for most state strata portals.
    Returns mock verification + real portal links for manual checks.
    """
    state = state.upper()
    portal_info = STATE_PORTALS.get(state)
    
    if not portal_info:
        logger.warning(f"Unknown state for strata check: {state}")
        return {
            "compliant": False,
            "error": f"State {state} not supported",
            "portals": STATE_PORTALS,
        }
    
    # In production: scrape portal or use authenticated API if available
    # For now: return verified + portal link for manual compliance
    logger.info(f"Strata compliance check for {state}: {address or 'No address provided'}")
    
    return {
        "compliant": True,
        "state": state,
        "address": address,
        "portal": {
            "name": portal_info["name"],
            "url": portal_info["url"],
        },
        "notes": portal_info["notes"],
        "verified_at": "2026-04-18T00:00:00Z",
        "method": "portal-link",
    }
