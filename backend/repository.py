from __future__ import annotations

import sqlite3
from datetime import UTC, datetime

from backend.models import SummaryResponse, TransactionRequest, TransactionResponse, TransactionType
from backend.ranking import calculate_abuse_penalty, calculate_score


def points_for(transaction_type: TransactionType, amount: float) -> int:
    points = int(round(amount))
    if transaction_type == TransactionType.refund:
        return -points
    if transaction_type == TransactionType.bonus:
        return min(points, 500)
    return points


class TransactionRepository:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def create_transaction(self, payload: TransactionRequest) -> tuple[dict, dict, bool]:
        created_at = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        points_delta = points_for(payload.type, payload.amount)

        try:
            self.connection.execute("BEGIN IMMEDIATE")
            self.connection.execute(
                """
                INSERT INTO transactions (
                    request_id, user_id, amount, transaction_type, points_delta, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    payload.request_id,
                    payload.user_id,
                    payload.amount,
                    payload.type.value,
                    points_delta,
                    created_at,
                ),
            )
            self._upsert_summary(payload.user_id, payload.type, points_delta, created_at)
            transaction = self._get_transaction_by_request_id(payload.request_id)
            summary = self.get_summary(payload.user_id)
            self.connection.execute("COMMIT")
            return transaction, summary, False
        except sqlite3.IntegrityError:
            self.connection.execute("ROLLBACK")
            transaction = self._get_transaction_by_request_id(payload.request_id)
            summary = self.get_summary(transaction["user_id"])
            return transaction, summary, True
        except Exception:
            self.connection.execute("ROLLBACK")
            raise

    def _upsert_summary(
        self,
        user_id: str,
        transaction_type: TransactionType,
        points_delta: int,
        created_at: str,
    ) -> None:
        purchase_increment = 1 if transaction_type == TransactionType.purchase else 0
        refund_increment = 1 if transaction_type == TransactionType.refund else 0
        bonus_increment = 1 if transaction_type == TransactionType.bonus else 0

        self.connection.execute(
            """
            INSERT INTO user_summaries (
                user_id, total_points, transaction_count, purchase_count,
                refund_count, bonus_count, last_transaction_at
            )
            VALUES (?, ?, 1, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                total_points = total_points + excluded.total_points,
                transaction_count = transaction_count + 1,
                purchase_count = purchase_count + excluded.purchase_count,
                refund_count = refund_count + excluded.refund_count,
                bonus_count = bonus_count + excluded.bonus_count,
                last_transaction_at = excluded.last_transaction_at
            """,
            (
                user_id,
                points_delta,
                purchase_increment,
                refund_increment,
                bonus_increment,
                created_at,
            ),
        )

    def _get_transaction_by_request_id(self, request_id: str) -> dict:
        row = self.connection.execute(
            """
            SELECT
                id,
                request_id,
                user_id,
                amount,
                transaction_type AS type,
                points_delta,
                created_at
            FROM transactions
            WHERE request_id = ?
            """,
            (request_id,),
        ).fetchone()
        if row is None:
            raise LookupError("Transaction was not found after write attempt")
        return dict(row)

    def get_summary(self, user_id: str) -> dict:
        row = self.connection.execute(
            """
            SELECT
                user_id,
                total_points,
                transaction_count,
                purchase_count,
                refund_count,
                bonus_count,
                last_transaction_at
            FROM user_summaries
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()
        if row is None:
            return {
                "user_id": user_id,
                "total_points": 0,
                "transaction_count": 0,
                "purchase_count": 0,
                "refund_count": 0,
                "bonus_count": 0,
                "last_transaction_at": None,
            }
        return dict(row)

    def get_ranking(self, limit: int) -> list[dict]:
        rows = self.connection.execute(
            """
            SELECT
                user_id,
                total_points,
                transaction_count,
                purchase_count,
                refund_count,
                bonus_count,
                last_transaction_at
            FROM user_summaries
            """
        ).fetchall()

        entries = []
        for row in rows:
            entry = dict(row)
            entry["score"] = calculate_score(row)
            entry["abuse_penalty"] = calculate_abuse_penalty(row)
            entries.append(entry)

        entries.sort(
            key=lambda item: (
                -item["score"],
                -item["total_points"],
                item["refund_count"],
                item["last_transaction_at"] or "",
                item["user_id"],
            )
        )

        ranked = []
        for index, entry in enumerate(entries[:limit], start=1):
            ranked.append({"rank": index, **entry})
        return ranked


def to_transaction_response(row: dict, duplicate: bool) -> TransactionResponse:
    return TransactionResponse(
        id=row["id"],
        requestId=row["request_id"],
        userId=row["user_id"],
        amount=row["amount"],
        type=row["type"],
        pointsDelta=row["points_delta"],
        createdAt=row["created_at"],
        duplicate=duplicate,
    )


def to_summary_response(row: dict) -> SummaryResponse:
    return SummaryResponse(
        userId=row["user_id"],
        totalPoints=row["total_points"],
        transactionCount=row["transaction_count"],
        purchaseCount=row["purchase_count"],
        refundCount=row["refund_count"],
        bonusCount=row["bonus_count"],
        lastTransactionAt=row["last_transaction_at"],
    )
