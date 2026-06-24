from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class TransactionType(StrEnum):
    purchase = "purchase"
    refund = "refund"
    bonus = "bonus"


UserId = Annotated[str, Field(pattern=r"^[A-Za-z0-9_-]{3,64}$")]
RequestId = Annotated[str, Field(min_length=6, max_length=100)]


class TransactionRequest(BaseModel):
    request_id: RequestId = Field(alias="requestId")
    user_id: UserId = Field(alias="userId")
    amount: Annotated[float, Field(gt=0, le=1_000_000)]
    type: TransactionType

    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)


class TransactionResponse(BaseModel):
    id: int
    request_id: str = Field(alias="requestId")
    user_id: str = Field(alias="userId")
    amount: float
    type: TransactionType
    points_delta: int = Field(alias="pointsDelta")
    created_at: str = Field(alias="createdAt")
    duplicate: bool = False

    model_config = ConfigDict(populate_by_name=True)


class SummaryResponse(BaseModel):
    user_id: str = Field(alias="userId")
    total_points: int = Field(alias="totalPoints")
    transaction_count: int = Field(alias="transactionCount")
    purchase_count: int = Field(alias="purchaseCount")
    refund_count: int = Field(alias="refundCount")
    bonus_count: int = Field(alias="bonusCount")
    last_transaction_at: str | None = Field(alias="lastTransactionAt")

    model_config = ConfigDict(populate_by_name=True)


class TransactionResult(BaseModel):
    transaction: TransactionResponse
    summary: SummaryResponse

    model_config = ConfigDict(populate_by_name=True)


class RankingEntry(SummaryResponse):
    score: int
    rank: int
    abuse_penalty: int = Field(alias="abusePenalty")

    model_config = ConfigDict(populate_by_name=True)
