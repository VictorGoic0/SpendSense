"""Shared JSON shaping for recommendation API responses."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict

from app.models import Recommendation

logger = logging.getLogger(__name__)


def attach_partner_offer_product_fields(rec_dict: Dict[str, Any], rec: Recommendation) -> None:
    """
    Merge product display fields from metadata_json.product_data onto rec_dict.

    partner_offer rows store rich product fields in metadata; list/user endpoints
    expose them as top-level keys so clients (e.g. ProductRecommendationCard) match
    GET /recommendations/{user_id}.
    """
    if rec.content_type != "partner_offer" or not rec.metadata_json:
        return
    try:
        metadata = json.loads(rec.metadata_json)
        product_data = metadata.get("product_data", {})
        rec_dict["product_id"] = rec.product_id
        rec_dict["product_name"] = product_data.get("product_name")
        rec_dict["short_description"] = product_data.get("short_description")
        rec_dict["benefits"] = product_data.get("benefits", [])
        rec_dict["partner_link"] = product_data.get("partner_link")
        rec_dict["disclosure"] = product_data.get("disclosure")
        rec_dict["typical_apy_or_fee"] = product_data.get("typical_apy_or_fee")
        rec_dict["partner_name"] = product_data.get("partner_name")
    except (json.JSONDecodeError, TypeError):
        logger.warning(
            "Failed to parse metadata for recommendation %s",
            rec.recommendation_id,
        )
