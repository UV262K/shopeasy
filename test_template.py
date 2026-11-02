import pathlib
import re
import textwrap

ROOT = pathlib.Path(__file__).parent


def test_template_inline_lambda_matches_source_file():
    """If this fails, run: python3 scripts/sync_lambda.py"""
    text = (ROOT / "infra" / "network-ecs.yaml").read_text()
    m = re.search(r" *# BEGIN order_processor\n(.*?) *# END order_processor\n", text, re.S)
    inline = textwrap.dedent(m.group(1)).strip()
    assert inline == (ROOT / "lambda" / "order_processor.py").read_text().strip()
    assert len(inline.encode()) <= 4096
