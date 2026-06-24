from __future__ import annotations

from sqlite3 import Row


def calculate_abuse_penalty(summary: Row | dict) -> int:
    bonus_count = int(summary["bonus_count"])
    transaction_count = int(summary["transaction_count"])
    repeated_bonus_penalty = max(0, bonus_count - 3) * 30
    high_frequency_penalty = max(0, transaction_count - 15) * 2
    return repeated_bonus_penalty + high_frequency_penalty


def calculate_score(summary: Row | dict) -> int:
    total_points = int(summary["total_points"])
    purchase_count = int(summary["purchase_count"])
    refund_count = int(summary["refund_count"])
    transaction_count = int(summary["transaction_count"])

    return (
        total_points
        + min(purchase_count, 20) * 5
        + min(transaction_count, 50)
        - refund_count * 25
        - calculate_abuse_penalty(summary)
    )
