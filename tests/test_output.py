import csv
import io
import json
from datetime import datetime, timezone

import pytest
from rich.console import Console

from pindo_cli import output
from pindo_cli.output import Column, format_value, parse_datetime, render, resolve_tz

COLS = [
    Column('id', 'ID'),
    Column('created_at', 'Created', kind='datetime'),
    Column('cost', 'Cost', kind='money'),
    Column('count', kind='number'),
    Column('meta'),
]
ROWS = [
    {'id': 'a', 'created_at': '2026-10-01T10:00:00.123456', 'cost': 0.006, 'count': 1200,
     'meta': {'k': 1}},
    {'id': 'b', 'created_at': '24-07-2020, 23:35:32', 'cost': None, 'count': 2.5, 'meta': None},
]


@pytest.mark.parametrize('value, expected', [
    ('2026-10-01T10:00:00.123456', datetime(2026, 10, 1, 10, 0, 0, 123456, tzinfo=timezone.utc)),
    ('2026-10-01T10:00:00Z', datetime(2026, 10, 1, 10, tzinfo=timezone.utc)),
    ('24-07-2020, 23:35:32', datetime(2020, 7, 24, 23, 35, 32, tzinfo=timezone.utc)),
    ('2026-10-01', datetime(2026, 10, 1, tzinfo=timezone.utc)),
    (1700000000, datetime(2023, 11, 14, 22, 13, 20, tzinfo=timezone.utc)),
    ('garbage', None),
    (None, None),
    ('', None),
])
def test_parse_datetime(value, expected):
    assert parse_datetime(value) == expected


def test_parse_datetime_passthrough():
    dt = datetime(2026, 1, 1, tzinfo=timezone.utc)
    assert parse_datetime(dt) is dt


def test_resolve_tz():
    assert resolve_tz('UTC') is timezone.utc
    assert resolve_tz(None) is not None
    assert resolve_tz('local') is not None
    assert str(resolve_tz('Africa/Kigali')) == 'Africa/Kigali'
    with pytest.raises(ValueError):
        resolve_tz('Mars/Olympus')


def test_format_value():
    assert format_value(None, Column('x')) == ''
    assert format_value('2026-10-01T10:00:00', Column('x', kind='datetime'), timezone.utc) == \
        '2026-10-01 10:00:00'
    assert format_value('nodate', Column('x', kind='datetime')) == 'nodate'
    assert format_value(0.006, Column('x', kind='money')) == '0.006'
    assert format_value(71421.953, Column('x', kind='money')) == '71,421.953'
    assert format_value(10, Column('x', kind='money')) == '10'
    assert format_value('n/a', Column('x', kind='money')) == 'n/a'
    assert format_value(1200, Column('x', kind='number')) == '1,200'
    assert format_value(2.5, Column('x', kind='number')) == '2.50'
    assert format_value('7', Column('x', kind='number')) == '7'
    assert format_value({'k': 1}, Column('x')) == '{"k": 1}'


def test_column_header():
    assert Column('created_at').header == 'Created At'
    assert Column('created_at', 'When').header == 'When'


def test_render_table_to_console():
    buf = io.StringIO()
    console = Console(file=buf, width=120, force_terminal=False)
    render(ROWS, COLS, 'table', console=console, title='T', tz=timezone.utc)
    text = buf.getvalue()
    assert 'T' in text and 'ID' in text and 'Created' in text
    assert '2026-10-01 10:00:00' in text
    assert '1,200' in text


def test_render_table_empty_caption():
    buf = io.StringIO()
    console = Console(file=buf, width=120, force_terminal=False)
    render([], COLS, 'table', console=console)
    assert 'No results.' in buf.getvalue()


def test_render_table_to_file(tmp_path):
    path = tmp_path / 'out.txt'
    render(ROWS, COLS, 'table', file=str(path))
    assert 'ID' in path.read_text()


def test_render_csv(capsys):
    render(ROWS, COLS, 'csv', tz=timezone.utc)
    out = capsys.readouterr().out
    rows = list(csv.reader(io.StringIO(out)))
    assert rows[0] == ['ID', 'Created', 'Cost', 'Count', 'Meta']
    assert rows[1] == ['a', '2026-10-01 10:00:00', '0.006', '1,200', '{"k": 1}']
    assert rows[2][2] == ''


def test_render_json_columns_only(capsys):
    render(ROWS, COLS[:2], 'json')
    data = json.loads(capsys.readouterr().out)
    assert data == [
        {'id': 'a', 'created_at': '2026-10-01T10:00:00.123456'},
        {'id': 'b', 'created_at': '24-07-2020, 23:35:32'},
    ]


def test_render_json_raw_to_file(tmp_path):
    path = tmp_path / 'out.json'
    rows = [{'id': 1, 'when': datetime(2026, 1, 1, tzinfo=timezone.utc), 'extra': True}]
    render(rows, COLS[:1], 'json', file=str(path), raw_json=True)
    data = json.loads(path.read_text())
    assert data == [{'id': 1, 'when': '2026-01-01T00:00:00+00:00', 'extra': True}]


def test_render_unknown_format():
    with pytest.raises(ValueError):
        render([], COLS, 'xml')


def test_summary_rows():
    rows = output.summary_rows({'total_cost': 1, 'sent': 2}, keys=['sent', 'total_cost'])
    assert rows == [{'field': 'Sent', 'value': 2}, {'field': 'Total Cost', 'value': 1}]
    rows = output.summary_rows({'a': 1}, labels=lambda k: k.upper())
    assert rows == [{'field': 'A', 'value': 1}]
