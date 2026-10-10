from fastapi import APIRouter, Depends

from .. import ai, flags
from ..deps import get_current_user
from ..models import User
from ..schemas import CategorizeIn, CategorizeOut

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/categorize", response_model=CategorizeOut)
def categorize(body: CategorizeIn, _: User = Depends(get_current_user)):
    """Suggest a category and flag unusual claims. Always answers with HTTP 200:
    if the AI is unavailable, ai_available is false and category is null, and
    the form falls back to manual selection."""
    result = ai.analyze_expense(body.description, body.amount)
    flagged, reason = flags.merge_flags(result, [flags.high_amount_reason(body.amount)])
    return CategorizeOut(
        category=result["category"],
        is_unusual=flagged,
        reason=reason,
        ai_available=result["ai_available"],
    )
