"""Full Shows API for Milestone 2.

Includes CRUD per PRODUCT_SPEC §14.3:
- GET/POST /workspaces/{workspace_id}/shows
- GET/PATCH /shows/{show_id}

Workspace scoped. Minimal for MVP (no delete on shows for safety).
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Show, Workspace
from ..schemas.shows import (
    ShowCreate,
    ShowUpdate,
    ShowResponse,
    ShowListResponse,
)

router = APIRouter(prefix="/shows", tags=["shows"])


def _get_workspace_or_404(workspace_id: UUID, db: Session) -> Workspace:
    ws = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return ws


def _get_show_or_404(show_id: UUID, db: Session) -> Show:
    show = db.query(Show).filter(Show.id == show_id).first()
    if not show:
        raise HTTPException(status_code=404, detail="Show not found")
    return show


@router.get("/workspaces/{workspace_id}/shows", response_model=ShowListResponse)
def list_shows(
    workspace_id: UUID,
    db: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
):
    """List shows for a workspace."""
    _get_workspace_or_404(workspace_id, db)  # validate ws exists
    query = db.query(Show).filter(Show.workspace_id == workspace_id).order_by(Show.created_at.desc())
    total = query.count()
    shows = query.offset(offset).limit(limit).all()
    return ShowListResponse(
        shows=[ShowResponse.model_validate(s) for s in shows],
        total=total,
    )


@router.post("/workspaces/{workspace_id}/shows", response_model=ShowResponse, status_code=status.HTTP_201_CREATED)
def create_show(
    workspace_id: UUID,
    show_in: ShowCreate,
    db: Session = Depends(get_db),
):
    """Create a new show in the workspace."""
    _get_workspace_or_404(workspace_id, db)
    # Basic slug uniqueness check (per model constraint)
    existing = (
        db.query(Show)
        .filter(Show.workspace_id == workspace_id, Show.slug == show_in.slug)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Show slug already exists in workspace")

    show = Show(
        workspace_id=workspace_id,
        **show_in.model_dump(),
    )
    db.add(show)
    db.commit()
    db.refresh(show)
    return ShowResponse.model_validate(show)


@router.get("/{show_id}", response_model=ShowResponse)
def get_show(show_id: UUID, db: Session = Depends(get_db)):
    show = _get_show_or_404(show_id, db)
    return ShowResponse.model_validate(show)


@router.patch("/{show_id}", response_model=ShowResponse)
def update_show(
    show_id: UUID,
    show_in: ShowUpdate,
    db: Session = Depends(get_db),
):
    show = _get_show_or_404(show_id, db)
    update_data = show_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(show, field, value)
    db.commit()
    db.refresh(show)
    return ShowResponse.model_validate(show)


@router.delete("/{show_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_show(show_id: UUID, db: Session = Depends(get_db)):
    """Delete show (M2 extension). Cascades via DB/models if episodes etc. have ondelete."""
    show = _get_show_or_404(show_id, db)
    db.delete(show)
    db.commit()
    return None
