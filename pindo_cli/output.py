"""
Output rendering shared by every report command.

A report is a list of row dicts plus an ordered list of :class:`Column`
definitions. :func:`render` writes it as a Rich table (default on a
terminal), CSV, or JSON, either to stdout or to ``--file``.
"""
import csv
import io
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Iterable, List, Optional, Sequence, TextIO

from rich.console import Console
from rich.table import Table

try:  # Python 3.9+
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    ZoneInfo = None  # type: ignore

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
    key: str                     # key in the row dict
    title: Optional[str] = None  # header text; defaults to key
    kind: str = 'text'           # text | number | money | datetime
    justify: str = 'left'
    style: Optional[str] = None

    @property
    def header(self) -> str:
        return self.title or self.key.replace('_', ' ').title()


def parse_datetime(value: Any) -> Optional[datetime]:
    """Best-effort parse of the timestamp strings the API returns.

    Naive timestamps are assumed to be UTC.
    """
    if value is None or value == '':
        return None
    if isinstance(value, datetime):
        dt: Optional[datetime] = value
    elif isinstance(value, (int, float)):
        dt = datetime.fromtimestamp(value, tz=timezone.utc)
    else:
        dt = _parse_datetime_text(str(value).strip())
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _parse_datetime_text(text: str) -> Optional[datetime]:
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


def resolve_tz(name: Optional[str]):
    """Return a tzinfo for ``name``; ``None``/'local' means the system zone."""
    if not name or name.lower() == 'local':
        return datetime.now().astimezone().tzinfo
    if name.upper() == 'UTC':
        return timezone.utc
    if ZoneInfo is None:  # pragma: no cover
        raise ValueError('Named timezones need Python 3.9+; use UTC or local.')
    try:
        return ZoneInfo(name)
    except Exception:
        raise ValueError('Unknown timezone: {}'.format(name))


def format_value(value: Any, column: Column, tz=None) -> str:
    if value is None:
        return ''
    formatter = _FORMATTERS.get(column.kind)
    if formatter is not None:
        return formatter(value, tz)
    if isinstance(value, (dict, list)):
        return json.dumps(value, default=str)
    return str(value)


def _format_datetime(value: Any, tz) -> str:
    dt = parse_datetime(value)
    if dt is None:
        return str(value)
    if tz is not None:
        dt = dt.astimezone(tz)
    return dt.strftime('%Y-%m-%d %H:%M:%S')


def _format_money(value: Any, tz) -> str:
    try:
        return '{:,.3f}'.format(float(value)).rstrip('0').rstrip('.')
    except (TypeError, ValueError):
        return str(value)


def _format_number(value: Any, tz) -> str:
    if isinstance(value, float):
        return '{:,.2f}'.format(value)
    if isinstance(value, int):
        return '{:,}'.format(value)
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


def build_table(rows: Sequence[dict], columns: Sequence[Column],
                title: Optional[str] = None, tz=None,
                caption: Optional[str] = None) -> Table:
    """Build (but don't print) a Rich table for ``rows``."""
    table = Table(title=title, caption=caption, expand=False)
    for col in columns:
        justify = col.justify
        if col.kind in ('number', 'money') and col.justify == 'left':
            justify = 'right'
        table.add_column(col.header, justify=justify, style=col.style, overflow='fold')
    for row in rows:
        table.add_row(*[format_value(row.get(c.key), c, tz) for c in columns])
    if not rows:
        table.caption = caption or 'No results.'
    return table


def render_csv(rows: Iterable[dict], columns: Sequence[Column], stream: TextIO,
               tz=None) -> None:
    writer = csv.writer(stream, lineterminator='\n')
    writer.writerow([c.header for c in columns])
    for row in rows:
        writer.writerow([format_value(row.get(c.key), c, tz) for c in columns])


def render_json(rows: Iterable[dict], columns: Sequence[Column], stream: TextIO,
                raw: bool = False) -> None:
    """Write rows as a JSON array. With ``raw`` the full row dicts are kept;
    otherwise only the report's columns are included."""
    out: List[dict] = []
    for row in rows:
        if raw:
            out.append({k: _json_safe(v) for k, v in row.items()})
        else:
            out.append({c.key: _json_safe(row.get(c.key)) for c in columns})
    json.dump(out, stream, indent=2, default=str)
    stream.write('\n')


def render(rows: Sequence[dict], columns: Sequence[Column], fmt: str = 'table',
           file: Optional[str] = None, title: Optional[str] = None,
           tz=None, console: Optional[Console] = None, raw_json: bool = False,
           caption: Optional[str] = None) -> None:
    """Render ``rows`` in ``fmt`` to stdout or ``file``."""
    if fmt not in FORMATS:
        raise ValueError('Unknown output format: {}'.format(fmt))
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


def summary_rows(data: dict, keys: Optional[Sequence[str]] = None,
                 labels: Optional[Callable[[str], str]] = None) -> List[dict]:
    """Turn a flat dict into ``[{'field': k, 'value': v}, ...]`` rows for
    key/value style output (balance, config show, analytics totals)."""
    keys = list(keys) if keys else list(data.keys())
    label = labels or (lambda k: k.replace('_', ' ').title())
    return [{'field': label(k), 'value': data.get(k)} for k in keys]


KV_COLUMNS = [Column('field', 'Field', style='bold'), Column('value', 'Value')]
