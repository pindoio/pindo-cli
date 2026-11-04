"""
Output rendering shared by every report command.

A report is a list of row dicts plus an ordered list of :class:`Column`
definitions. :func:`render` writes it as a Rich table (default on a
terminal), CSV, or JSON, either to stdout or to ``--file``.
"""

from __future__ import annotations

import csv
import io
import json
import sys
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone, tzinfo
from typing import Any, TextIO
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from rich.console import Console, JustifyMethod
from rich.table import Table

FORMATS = ('table', 'csv', 'json')

# Date formats the backend has been seen to use.
_DATE_FORMATS = (
    '%Y-%m-%dT%H:%M:%S.%f',
    '%Y-%m-%dT%H:%M:%S',
    '%Y-%m-%d %H:%M:%S',
    '%d-%m-%Y, %H:%M:%S',
    '%Y-%m-%d',
)


@dataclass
class Column:
    key: str  # key in the row dict
    title: str | None = None  # header text; defaults to key
    kind: str = 'text'  # text | number | money | datetime
    justify: JustifyMethod = 'left'
    style: str | None = None

    @property
    def header(self) -> str:
        return self.title or self.key.replace('_', ' ').title()


def parse_datetime(value: Any) -> datetime | None:
    """Best-effort parse of the timestamp strings the API returns.

    Naive timestamps are assumed to be UTC.
    """
    if value is None or value == '':
        return None
    if isinstance(value, datetime):
        dt: datetime | None = value
    elif isinstance(value, (int, float)):
        dt = datetime.fromtimestamp(value, tz=timezone.utc)
    else:
        dt = _parse_datetime_text(str(value).strip())
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _parse_datetime_text(text: str) -> datetime | None:
    if text.endswith('Z'):
        text = text[:-1] + '+00:00'
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        pass
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def resolve_tz(name: str | None) -> tzinfo | None:
    """Return a tzinfo for ``name``; ``None``/'local' means the system zone."""
    if not name or name.lower() == 'local':
        return datetime.now().astimezone().tzinfo
    if name.upper() == 'UTC':
        return timezone.utc
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError):
        raise ValueError(f'Unknown timezone: {name}') from None


def format_value(value: Any, column: Column, tz: tzinfo | None = None) -> str:
    if value is None:
        return ''
    formatter = _FORMATTERS.get(column.kind)
    if formatter is not None:
        return formatter(value, tz)
    if isinstance(value, (dict, list)):
        return json.dumps(value, default=str)
    return str(value)


def _format_datetime(value: Any, tz: tzinfo | None) -> str:
    dt = parse_datetime(value)
    if dt is None:
        return str(value)
    if tz is not None:
        dt = dt.astimezone(tz)
    return dt.strftime('%Y-%m-%d %H:%M:%S')


def _format_money(value: Any, tz: tzinfo | None) -> str:
    try:
        return f'{float(value):,.3f}'.rstrip('0').rstrip('.')
    except (TypeError, ValueError):
        return str(value)


def _format_number(value: Any, tz: tzinfo | None) -> str:
    if isinstance(value, float):
        return f'{value:,.2f}'
    if isinstance(value, int):
        return f'{value:,}'
    return str(value)


_FORMATTERS = {
    'datetime': _format_datetime,
    'money': _format_money,
    'number': _format_number,
}


def _json_safe(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def build_table(
    rows: Sequence[dict],
    columns: Sequence[Column],
    title: str | None = None,
    tz: tzinfo | None = None,
    caption: str | None = None,
) -> Table:
    """Build (but don't print) a Rich table for ``rows``."""
    table = Table(title=title, caption=caption, expand=False)
    for col in columns:
        justify: JustifyMethod = col.justify
        if col.kind in ('number', 'money') and col.justify == 'left':
            justify = 'right'
        table.add_column(col.header, justify=justify, style=col.style, overflow='fold')
    for row in rows:
        table.add_row(*[format_value(row.get(c.key), c, tz) for c in columns])
    if not rows:
        table.caption = caption or 'No results.'
    return table


def render_csv(rows: Iterable[dict], columns: Sequence[Column], stream: TextIO, tz=None) -> None:
    writer = csv.writer(stream, lineterminator='\n')
    writer.writerow([c.header for c in columns])
    for row in rows:
        writer.writerow([format_value(row.get(c.key), c, tz) for c in columns])


def render_json(
    rows: Iterable[dict], columns: Sequence[Column], stream: TextIO, raw: bool = False
) -> None:
    """Write rows as a JSON array. With ``raw`` the full row dicts are kept;
    otherwise only the report's columns are included."""
    out: list[dict[str, Any]] = []
    for row in rows:
        if raw:
            out.append({k: _json_safe(v) for k, v in row.items()})
        else:
            out.append({c.key: _json_safe(row.get(c.key)) for c in columns})
    json.dump(out, stream, indent=2, default=str)
    stream.write('\n')


def render(
    rows: Sequence[dict],
    columns: Sequence[Column],
    fmt: str = 'table',
    file: str | None = None,
    title: str | None = None,
    tz=None,
    console: Console | None = None,
    raw_json: bool = False,
    caption: str | None = None,
) -> None:
    """Render ``rows`` in ``fmt`` to stdout or ``file``."""
    if fmt not in FORMATS:
        raise ValueError(f'Unknown output format: {fmt}')
    rows = list(rows)

    if fmt == 'table':
        table = build_table(rows, columns, title, tz, caption)
        if file:
            buf = io.StringIO()
            Console(file=buf, width=200, force_terminal=False).print(table)
            _write(file, buf.getvalue())
        else:
            (console or Console()).print(table)
        return

    buf = io.StringIO()
    if fmt == 'csv':
        render_csv(rows, columns, buf, tz=tz)
    else:
        render_json(rows, columns, buf, raw=raw_json)
    if file:
        _write(file, buf.getvalue())
    else:
        sys.stdout.write(buf.getvalue())
        sys.stdout.flush()


def _write(path: str, text: str) -> None:
    with open(path, 'w', encoding='utf-8', newline='') as fh:
        fh.write(text)


def summary_rows(
    data: dict, keys: Sequence[str] | None = None, labels: Callable[[str], str] | None = None
) -> list[dict[str, Any]]:
    """Turn a flat dict into ``[{'field': k, 'value': v}, ...]`` rows for
    key/value style output (balance, config show, analytics totals)."""
    keys = list(keys) if keys else list(data.keys())
    label = labels or (lambda k: k.replace('_', ' ').title())
    return [{'field': label(k), 'value': data.get(k)} for k in keys]


KV_COLUMNS = [Column('field', 'Field', style='bold'), Column('value', 'Value')]
