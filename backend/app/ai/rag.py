from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import logging

logger = logging.getLogger(__name__)

# NDIS 2026 Price Guide + AusClean Pro knowledge base
KNOWLEDGE_BASE = """
AusClean Pro - Enterprise Cleaning Services (2026)

SERVICES & PRICING (AUD, incl. 10% GST):
- Regular Clean: $89 base + $25/extra bedroom + $30/extra bathroom
- Deep Clean: $179 base (4hrs, 2 cleaners)
- End of Lease: $229 base (bond-back guarantee, NSW/VIC/QLD)
- Carpet Clean: $149 base (steam cleaning, up to 3 rooms)
- Window Clean: $119 base (interior + exterior, ground floor)
- Strata/Common Area: $199 base (compliance check included)

NDIS PRICING (2026 NDIS Price Guide):
- Standard Cleaning (Assistance with Daily Life): $64.78/hr (weekday)
- Complex Cleaning (SIL): $78.94/hr
- Travel: $15.56/km (non-metro), $12.34/km (metro)
- Weekend rates: 1.5x weekday, Public Holidays: 2x weekday

STATE COMPLIANCE:
- NSW: Fair Trading, Strata Schemes Management Act 2015
- VIC: Consumer Affairs Victoria, Owners Corporations Act 2006
- QLD: Body Corporate (BCCM Act 1997)
- All states: 10% GST included, ABN displayed

BOOKING POLICY:
- Free cancellation up to 24hrs before
- No-show fee: 50% of booking amount
- Bond-back guarantee for end-of-lease cleans
- All cleaners police-checked, insured, and trained

CONTACT: support@auscleanpro.com.au | 1300-CLEAN-AU
"""

def get_rag_chain():
    """Create RAG chain for AusClean Pro knowledge retrieval."""
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""You are the AusClean Pro AI assistant (2026). Use the following knowledge base to answer questions:

{KNOWLEDGE_BASE}

Rules:
- Always quote prices in AUD with GST included
- Mention NDIS pricing if relevant
- Refer to state-specific compliance for strata questions
- Be professional, friendly, and concise
- If unsure, direct customer to support@auscleanpro.com.au"""),
        ("human", "{question}"),
    ])
    
    chain = prompt | llm | StrOutputParser()
    return chain
