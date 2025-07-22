from typing import List
from fastapi import APIRouter, HTTPException

router = APIRouter()

# Sample in-memory data for demonstration
items_db = [
    {"id": 1, "name": "Item 1", "description": "First sample item"},
    {"id": 2, "name": "Item 2", "description": "Second sample item"},
]


@router.get("/")
async def get_items() -> List[dict]:
    return items_db


@router.get("/{item_id}")
async def get_item(item_id: int) -> dict:
    for item in items_db:
        if item["id"] == item_id:
            return item
    raise HTTPException(status_code=404, detail="Item not found")


@router.post("/")
async def create_item(name: str, description: str = None) -> dict:
    new_id = max([item["id"] for item in items_db]) + 1 if items_db else 1
    new_item = {"id": new_id, "name": name, "description": description}
    items_db.append(new_item)
    return new_item


@router.delete("/{item_id}")
async def delete_item(item_id: int) -> dict:
    for i, item in enumerate(items_db):
        if item["id"] == item_id:
            deleted_item = items_db.pop(i)
            return {"message": f"Item {item_id} deleted", "item": deleted_item}
    raise HTTPException(status_code=404, detail="Item not found")