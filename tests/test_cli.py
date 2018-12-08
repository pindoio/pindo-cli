from click.testing import CliRunner
import pytest

from pindo_cli import


@pytest.fixture(scope="module")
def runner():
    return CliRunner()

def test_named_hello(runner):
    result = runner.invoke(hll.main, ['--name','Amy'])
    assert result.exit_code == 0
    assert result.output == 'Hello Amy!\n'