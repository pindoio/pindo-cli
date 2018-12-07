import pytest
from click.testing import CliRunner

import pindo_cli


@pytest.fixture(scope="module")
def runner():
    return CliRunner()


def test_pindo_cli(runner):
    result = runner.invoke(pindo_cli.cli, ['--help'])
    assert result.exit_code == 0
    assert 'Pindo CLI' in result.output


# def test_command_token(runner):
#     result = runner.invoke(pindo_cli.token, ['-u', 'kenessa', '-p', 'bar'])
#     assert result.exit_code == 0
#     assert 'message' in result.output


# def test_command_register(runner):
#     result = runner.invoke(
#         pindo_cli.register,
#         ['-u', 'kenessa', '-e', 'remy@pindo.io', '-p', 'bar'])
#     assert result.exit_code == 0
#     assert 'message' in result.output


# def test_command_sms(runner):
#     result = runner.invoke(
#         pindo_cli.sms, [
#             '--token', 'oeiroeoeioeoiroe',
#             '--to', '+250785383100',
#             '--text', 'Hello Pindo',
#             '--sender', 'Pindo'
#         ])
#     assert result.exit_code == 0
#     assert 'message' in result.output
