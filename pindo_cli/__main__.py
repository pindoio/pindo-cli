"""Allow ``python -m pindo_cli``."""

from pindo_cli.cli import cli

if __name__ == '__main__':  # pragma: no cover
    cli(prog_name='pindo')
