from __future__ import annotations

"""Voice input router: parse spoken transcripts into transaction fields."""

from fastapi import APIRouter

from backend.schemas.voice import VoiceParseRequest, VoiceParseResponse
from backend.services.voice_service import parse_transcript

router = APIRouter(prefix="/voice", tags=["voice"])


@router.post("/parse", response_model=VoiceParseResponse)
async def parse_voice_transcript(payload: VoiceParseRequest) -> VoiceParseResponse:
    """Parse a voice transcript and return structured transaction fields.

    Args:
        payload: Request body containing the raw transcript string.

    Returns:
        Extracted fields (amount, currency, description, merchant, date, etc.)
        plus a confidence score.
    """
    return parse_transcript(payload.transcript)
