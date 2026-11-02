#!/usr/bin/env python3
"""Copy lambda/order_processor.py into the inline ZipFile block of the CloudFormation
template, so the Lambda is tested as a normal file but deployed without packaging.

Run after editing the Lambda:  python3 scripts/sync_lambda.py
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "lambda" / "order_processor.py"
TEMPLATE = ROOT / "infra" / "network-ecs.yaml"
INDENT = " " * 10
PATTERN = re.compile(r"(?P<start> *# BEGIN order_processor\n)(?P<body>.*?)(?P<end> *# END order_processor\n)", re.S)


def inline_block(code: str) -> str:
    lines = [(INDENT + line) if line.strip() else "" for line in code.rstrip("\n").split("\n")]
    return "\n".join(lines) + "\n"


def main():
    code = SRC.read_text()
    if len(code.encode()) > 4096:
        sys.exit(f"{SRC} is {len(code.encode())} bytes; CloudFormation inline code is limited to 4096")
    text = TEMPLATE.read_text()
    if not PATTERN.search(text):
        sys.exit("BEGIN/END order_processor markers not found in the template")
    new = PATTERN.sub(lambda m: m.group("start") + inline_block(code) + m.group("end"), text)
    TEMPLATE.write_text(new)
    print("Template updated from", SRC.relative_to(ROOT))


if __name__ == "__main__":
    main()
