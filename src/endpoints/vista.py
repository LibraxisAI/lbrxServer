"""VISTA-specific helper endpoints.

At the time of writing the desktop application *VISTA* expects a convenience
route that returns a SOAP-formatted summary generated from visit data and an
optional transcription.  We simply proxy the request to the general Chat API
using a purpose-built system prompt.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ..models import ChatCompletionRequest, ChatMessage  # Re-use existing types
from ..model_router import create_chat_completion
from ..config import config

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Pydantic schemas – keep them minimal and flexible for the desktop app
# ---------------------------------------------------------------------------


class PatientData(BaseModel):
    name: str
    species: str
    breed: str | None = None
    age: str
    weight: str | None = None
    ownerName: str = Field(alias="owner_name")


class VisitData(BaseModel):
    visitType: str = Field(alias="visit_type")
    reasonForVisit: str | None = Field(default=None, alias="reason_for_visit")
    transcription: str | None = None
    notes: str | None = None
    veterinarian: str


class SOAPRequest(BaseModel):
    patientData: PatientData = Field(alias="patient_data")
    visitData: VisitData = Field(alias="visit_data")
    # Optional model override
    model: str | None = None


@router.post("/vista/soap", tags=["VISTA"])
async def generate_soap(payload: SOAPRequest) -> Dict[str, Any]:
    """Generate SOAP protocol summary tailored for VISTA.

    Internally forwards the call to /v1/chat/completions with a crafted
    prompt so we can leverage all existing safety / rate limiting logic.
    """

    # Build prompt (identical to previous TS implementation)
    p = payload
    prompt = (
        "Na podstawie poniższych informacji, przygotuj profesjonalny protokół SOAP dla wizyty weterynaryjnej:\n\n"
        f"DANE PACJENTA:\n- Imię: {p.patientData.name}\n- Gatunek: {p.patientData.species}\n"
        f"- Rasa: {p.patientData.breed or 'Nie podano'}\n- Wiek: {p.patientData.age}\n"
        f"- Waga: {p.patientData.weight or 'Nie podano'}\n- Właściciel: {p.patientData.ownerName}\n\n"
        f"DANE WIZYTY:\n- Typ wizyty: {p.visitData.visitType}\n- Powód wizyty: {p.visitData.reasonForVisit or 'Nie podano'}\n"
        f"- Weterynarz: {p.visitData.veterinarian}\n\n"
    )

    if p.visitData.transcription:
        prompt += f"TRANSKRYPCJA WIZYTY:\n{p.visitData.transcription}\n\n"

    if p.visitData.notes:
        prompt += f"NOTATKI WEWNĘTRZNE:\n{p.visitData.notes}\n\n"

    prompt += (
        "Stwórz protokół SOAP w następującym formacie JSON:\n{\n  \"subjective\": \"...\",\n  \"objective\": \"...\",\n  \"assessment\": \"...\",\n  \"plan\": \"...\"\n}\n\n"
        "WYMAGANIA:\n- Używaj profesjonalnej terminologii weterynaryjnej\n"
        "- Bądź konkretny i precyzyjny\n- Każda sekcja powinna zawierać relevantne informacje\n"
        "- Jeśli brakuje informacji, napisz co należałoby jeszcze zbadać\n"
        "- Odpowiedź MUSI być w formacie JSON jak podano wyżej"
    )

    system_prompt = (
        "Jesteś doświadczonym weterynarzem. Twoim zadaniem jest tworzenie "
        "profesjonalnych protokołów SOAP na podstawie dostępnych informacji."
    )

    request_body = ChatCompletionRequest(
        model=p.model or config.default_model,
        messages=[
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=prompt),
        ],
        temperature=0.3,
        max_tokens=1000,
        stream=False,
    )

    try:
        result = await create_chat_completion(request_body)
    except Exception as exc:
        logger.exception("SOAP generation failed")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))

    return result
