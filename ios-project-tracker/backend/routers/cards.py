"""Card CRUD endpoints."""

from fastapi import APIRouter, HTTPException, Header

from config import settings
from models import Card, CardCreate, CardStatus, CardUpdate
from storage import storage
from routers.websocket_router import broadcast

router = APIRouter()


def verify_token(authorization: str = Header()):
    token = authorization.replace("Bearer ", "")
    if token != settings.auth_token:
        raise HTTPException(status_code=401, detail="Invalid auth token")


@router.get("")
async def list_cards(
    status: CardStatus | None = None,
    authorization: str = Header(default=""),
):
    verify_token(authorization)
    cards = storage.get_cards()
    if status:
        cards = [c for c in cards if c.status == status]
    return {"cards": [c.model_dump(mode="json") for c in cards]}


@router.post("", status_code=201)
async def create_card(body: CardCreate, authorization: str = Header(default="")):
    verify_token(authorization)
    card = Card(**body.model_dump())
    storage.create_card(card)
    await broadcast("card_created", card.model_dump(mode="json"))
    return card.model_dump(mode="json")


@router.get("/{card_id}")
async def get_card(card_id: str, authorization: str = Header(default="")):
    verify_token(authorization)
    card = storage.get_card(card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    return card.model_dump(mode="json")


@router.patch("/{card_id}")
async def update_card(
    card_id: str, body: CardUpdate, authorization: str = Header(default="")
):
    verify_token(authorization)
    card = storage.update_card(card_id, **body.model_dump(exclude_unset=True))
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    await broadcast("card_updated", card.model_dump(mode="json"))
    return card.model_dump(mode="json")


@router.delete("/{card_id}", status_code=204)
async def delete_card(card_id: str, authorization: str = Header(default="")):
    verify_token(authorization)
    if not storage.delete_card(card_id):
        raise HTTPException(status_code=404, detail="Card not found")
    await broadcast("card_deleted", {"id": card_id})
