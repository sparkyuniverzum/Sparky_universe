from __future__ import annotations

import calendar
from datetime import date, timedelta
from typing import Any, Dict, List, Tuple


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _add_months(current: date, months: int) -> date:
    month_index = current.month - 1 + months
    year = current.year + month_index // 12
    month = month_index % 12 + 1
    day = min(current.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def expand_dates(
    *,
    start_date: str | None,
    end_date: str | None,
    step: int,
    unit: str,
) -> Tuple[Dict[str, Any] | None, str | None]:
    start = _parse_date(start_date)
    end = _parse_date(end_date)
    if not start or not end:
        return None, "Provide valid start and end dates."
    if start > end:
        return None, "Start date must be before end date."
    if step <= 0:
        return None, "Step must be a positive integer."
    if unit not in {"days", "weeks", "months"}:
        return None, "Unsupported unit."

    dates: List[str] = []
    current = start
    max_items = 5000

    while current <= end:
        dates.append(current.isoformat())
        if len(dates) > max_items:
            return None, "Too many dates."
        if unit == "days":
            current += timedelta(days=step)
        elif unit == "weeks":
            current += timedelta(weeks=step)
        else:
            current = _add_months(current, step)

    return {
        "count": len(dates),
        "start": start.isoformat(),
        "end": end.isoformat(),
        "step": step,
        "unit": unit,
        "dates": dates,
    }, None
