"""Inngest workflow definitions for AusClean Pro.

Workflows:
- booking.confirmed → no-show detection + churn prediction
- booking.completed → review request + loyalty points
- review.created → sentiment analysis + churn scoring
"""
from typing import Any

# Inngest workflow patterns (pseudocode - requires inngest SDK setup)

WORKFLOWS = {
    "booking.no-show": {
        "id": "no-show-churn-workflow",
        "steps": [
            {
                "name": "detect-no-show",
                "description": "Check if customer missed booking",
                "action": "Check booking status 2hrs after booking_date",
            },
            {
                "name": "predict-churn",
                "description": "Calculate churn probability after no-show",
                "action": "Call AI churn prediction with customer history",
                "threshold": 0.7,  # Trigger retention if > 70%
            },
            {
                "name": "retention-campaign",
                "description": "Trigger retention campaign for high-risk customers",
                "condition": "churn_score > 0.7",
                "action": "Send discount email + SMS follow-up",
            },
            {
                "name": "mas-factory",
                "description": "Multi-Agent System for personalized retention",
                "action": "Generate personalized offer based on booking history",
            },
        ],
    },
    "booking.completed": {
        "id": "post-completion-workflow",
        "steps": [
            {
                "name": "send-review-request",
                "description": "Email customer asking for review",
                "delay": "2h",
            },
            {
                "name": "award-loyalty-points",
                "description": "Add points to customer loyalty balance",
                "action": "points = booking_amount / 10",
            },
            {
                "name": "update-xero",
                "description": "Mark invoice as paid in Xero",
                "action": "Update invoice status to PAID",
            },
        ],
    },
    "review.created": {
        "id": "review-analysis-workflow",
        "steps": [
            {
                "name": "sentiment-analysis",
                "description": "Analyze review sentiment with LLM",
                "action": "Call OpenAI sentiment analysis",
            },
            {
                "name": "churn-scoring",
                "description": "Update customer churn probability",
                "action": "Recalculate churn with new review data",
            },
            {
                "name": "alert-if-negative",
                "description": "Alert team if rating <= 2",
                "condition": "rating <= 2",
                "action": "Send Slack notification + create support ticket",
            },
        ],
    },
}
