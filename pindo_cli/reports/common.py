"""
Shared plumbing for report commands: the ``report`` group, the common option
set, and helpers for date ranges and output.
"""

from __future__ import annotations

import functools
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone, tzinfo
from typing import Any

import click

from pindo_cli.output import FORMATS, parse_datetime, resolve_tz

DEFAULT_DAYS = 7
DEFAULT_PER_PAGE = 50


@click.group()
def report() -> None:
    """
    Pull reports from your Pindo account.

    Every report accepts --from/--to (dates, default: last 7 days),
    --output table|csv|json and --file to save the result. Use --all to
    fetch every page instead of just the first.
    """


@dataclass
class ReportOptions:
    date_from: date | None
    date_to: date | None
    page: int
    per_page: int
    all_pages: bool
    output: str
    file: str | None
    tz: tzinfo | None

    @property
    def max_pages(self) -> int | None:
        return None if self.all_pages else 1

    def params(self, from_key: str = 'from', to_key: str = 'to') -> dict[str, Any]:
        """Query params understood by the backend list endpoints."""
        p: dict[str, Any] = {'page': self.page, 'per_page': self.per_page}
        if self.date_from:
            p[from_key] = self.date_from.isoformat()
        if self.date_to:
            p[to_key] = self.date_to.isoformat()
        return p

    def in_range(self, value: Any) -> bool:
        """Client-side filter for endpoints that ignore date params."""
        if not (self.date_from or self.date_to):
            return True
        dt = parse_datetime(value)
        if dt is None:
            return True
        d = dt.astimezone(self.tz).date()
        if self.date_from and d < self.date_from:
            return False
        return not (self.date_to and d > self.date_to)


def _parse_date(ctx: click.Context, param: click.Parameter, value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):  # datetime is a date subclass: check it first
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip().lower()
    today = datetime.now().date()
    if text == 'today':
        return today
    if text == 'yesterday':
        return today - timedelta(days=1)
    if text.endswith('d') and text[:-1].isdigit():  # e.g. 30d
        return today - timedelta(days=int(text[:-1]))
    try:
        return datetime.fromisoformat(text).date()
    except ValueError:
        raise click.BadParameter(
            'use YYYY-MM-DD, "today", "yesterday" or "<n>d" (e.g. 30d)', ctx=ctx, param=param
        ) from None


def report_options(
    default_days: int = DEFAULT_DAYS,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator adding the shared report options and passing a
    :class:`ReportOptions` as the ``opts`` keyword argument."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @click.option(
            '--from',
            'date_from',
            callback=_parse_date,
            metavar='DATE',
            help='Start date (YYYY-MM-DD, today, yesterday, 30d). '
            f'Default: {default_days} days ago.',
        )
        @click.option(
            '--to',
            'date_to',
            callback=_parse_date,
            metavar='DATE',
            help='End date (inclusive). Default: today.',
        )
        @click.option(
            '--page',
            default=1,
            type=click.IntRange(min=1),
            show_default=True,
            help='Page to fetch.',
        )
        @click.option(
            '--per-page',
            default=DEFAULT_PER_PAGE,
            type=click.IntRange(1, 500),
            show_default=True,
            help='Rows per page.',
        )
        @click.option(
            '--all',
            'all_pages',
            is_flag=True,
            default=False,
            help='Fetch every page (ignores --page).',
        )
        @click.option(
            '--output',
            '-o',
            type=click.Choice(FORMATS),
            default='table',
            show_default=True,
            help='Output format.',
        )
        @click.option(
            '--file',
            '-f',
            default=None,
            metavar='PATH',
            help='Write the output to a file instead of stdout.',
        )
        @click.option(
            '--tz',
            default=None,
            metavar='ZONE',
            help='Timezone for dates, e.g. Africa/Kigali or UTC. Default: local.',
        )
        @functools.wraps(func)
        def wrapper(
            *args: Any,
            date_from: date | None,
            date_to: date | None,
            page: int,
            per_page: int,
            all_pages: bool,
            output: str,
            file: str | None,
            tz: str | None,
            **kwargs: Any,
        ) -> Any:
            tzinfo = resolve_tz(tz)
            today = datetime.now(timezone.utc).astimezone(tzinfo).date()
            if date_from is None and date_to is None and default_days:
                date_from = today - timedelta(days=default_days)
                date_to = today
            elif date_to is None and date_from is not None:
                date_to = today
            if date_from and date_to and date_from > date_to:
                raise click.UsageError('--from must not be after --to.')
            opts = ReportOptions(
                date_from=date_from,
                date_to=date_to,
                page=page,
                per_page=per_page,
                all_pages=all_pages,
                output=output,
                file=file,
                tz=tzinfo,
            )
            return func(*args, opts=opts, **kwargs)

        return wrapper

    return decorator
