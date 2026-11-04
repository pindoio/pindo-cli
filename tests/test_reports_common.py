from datetime import date, datetime, timedelta, timezone

import click
from click.testing import CliRunner

from pindo_cli.reports.common import ReportOptions, report, report_options

captured = {}


@report.command('dummy')
@report_options(default_days=7)
def dummy(opts):
    captured['opts'] = opts
    click.echo('ok')


@report.command('nodefault')
@report_options(default_days=0)
def nodefault(opts):
    captured['opts'] = opts
    click.echo('ok')


def invoke(*args):
    result = CliRunner().invoke(report, list(args))
    return result, captured.get('opts')


def test_defaults():
    result, opts = invoke('dummy', '--tz', 'UTC')
    assert result.exit_code == 0, result.output
    today = datetime.now(timezone.utc).date()
    assert opts.date_to == today
    assert opts.date_from == today - timedelta(days=7)
    assert opts.page == 1
    assert opts.per_page == 50
    assert opts.all_pages is False
    assert opts.max_pages == 1
    assert opts.output == 'table'
    assert opts.file is None
    assert opts.tz is timezone.utc


def test_no_default_range():
    result, opts = invoke('nodefault')
    assert result.exit_code == 0
    assert opts.date_from is None
    assert opts.date_to is None
    assert opts.params() == {'page': 1, 'per_page': 50}


def test_explicit_dates_and_params():
    result, opts = invoke(
        'dummy',
        '--from',
        '2026-10-01',
        '--to',
        '2026-10-31',
        '--page',
        '3',
        '--per-page',
        '10',
        '-o',
        'csv',
        '-f',
        'x.csv',
    )
    assert result.exit_code == 0, result.output
    assert opts.date_from == date(2026, 10, 1)
    assert opts.date_to == date(2026, 10, 31)
    assert opts.params() == {'page': 3, 'per_page': 10, 'from': '2026-10-01', 'to': '2026-10-31'}
    assert opts.params('start', 'end')['start'] == '2026-10-01'
    assert opts.output == 'csv'
    assert opts.file == 'x.csv'


def test_relative_dates():
    today = datetime.now().date()
    _, opts = invoke('dummy', '--from', '30d')
    assert opts.date_from == today - timedelta(days=30)
    assert opts.date_to == today
    _, opts = invoke('dummy', '--from', 'yesterday', '--to', 'today')
    assert opts.date_from == today - timedelta(days=1)
    assert opts.date_to == today


def test_all_pages():
    _, opts = invoke('dummy', '--all')
    assert opts.all_pages is True
    assert opts.max_pages is None


def test_bad_date():
    result, _ = invoke('dummy', '--from', 'nope')
    assert result.exit_code == 2
    assert 'YYYY-MM-DD' in result.output


def test_from_after_to():
    result, _ = invoke('dummy', '--from', '2026-10-31', '--to', '2026-10-01')
    assert result.exit_code == 2
    assert '--from must not be after --to' in result.output


def test_bad_tz():
    result, _ = invoke('dummy', '--tz', 'Mars/Olympus')
    assert result.exit_code != 0
    assert 'Unknown timezone' in str(result.exception) or 'Unknown timezone' in result.output


def test_in_range_filter():
    opts = ReportOptions(
        date(2026, 10, 1), date(2026, 10, 31), 1, 50, False, 'table', None, timezone.utc
    )
    assert opts.in_range('2026-10-15T00:00:00') is True
    assert opts.in_range('2026-09-30T23:59:59') is False
    assert opts.in_range('2026-11-01T00:00:00') is False
    assert opts.in_range('not a date') is True
    opts = ReportOptions(None, None, 1, 50, False, 'table', None, timezone.utc)
    assert opts.in_range('2020-01-01') is True
