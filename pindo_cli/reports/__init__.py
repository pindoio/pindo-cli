"""
``pindo report`` — reporting commands.

Each report lives in its own module under this package and registers itself
on the :data:`report` group. Shared options (date range, pagination, output
format) come from :func:`report_options` so every report behaves the same.
"""

from pindo_cli.reports.common import report, report_options

__all__ = ['report', 'report_options']
