"""Tests AWS-facing code against moto (a fake AWS account), so no real account is needed."""
import importlib.util
import json
import pathlib

import pytest

boto3 = pytest.importorskip("boto3")
moto = pytest.importorskip("moto")
mock_aws = moto.mock_aws

ROOT = pathlib.Path(__file__).parent
REGION = "ap-southeast-2"


@pytest.fixture(autouse=True)
def fake_aws_env(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test")
    monkeypatch.setenv("AWS_DEFAULT_REGION", REGION)


def make_tables_and_bucket():
    ddb = boto3.client("dynamodb", region_name=REGION)
    for name, key in (("products", "product_id"), ("orders", "order_id")):
        ddb.create_table(
            TableName=name,
            AttributeDefinitions=[{"AttributeName": key, "AttributeType": "S"}],
            KeySchema=[{"AttributeName": key, "KeyType": "HASH"}],
            BillingMode="PAY_PER_REQUEST",
        )
    boto3.client("s3", region_name=REGION).create_bucket(
        Bucket="data", CreateBucketConfiguration={"LocationConstraint": REGION}
    )


@mock_aws
def test_seed_script_then_app_serves_products_and_stores_orders(monkeypatch):
    make_tables_and_bucket()
    monkeypatch.setenv("PRODUCTS_TABLE", "products")
    monkeypatch.setenv("DATA_BUCKET", "data")
    monkeypatch.setenv("AWS_REGION", REGION)

    spec = importlib.util.spec_from_file_location("seed", ROOT / "scripts" / "seed_products.py")
    seed = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(seed)
    seed.main()

    keys = [o["Key"] for o in boto3.client("s3", region_name=REGION).list_objects_v2(Bucket="data")["Contents"]]
    assert "images/p-001.svg" in keys and len(keys) == 12

    from app import app
    from store import DynamoStore

    app.config["STORE"] = DynamoStore("products", "orders", "data", REGION)
    client = app.test_client()
    items = client.get("/api/products").get_json()
    assert len(items) == 12
    assert isinstance(items[0]["price_inr"], int)
    assert items[0]["image_url"].startswith("https://") and "images/p-001.svg" in items[0]["image_url"]

    response = client.post("/api/checkout", json={"items": [{"product_id": "p-001", "qty": 2}]})
    assert response.status_code == 201
    saved = boto3.resource("dynamodb", region_name=REGION).Table("orders").get_item(
        Key={"order_id": response.get_json()["order_id"]})["Item"]
    assert int(saved["total_inr"]) == 2 * 2499 + 99
    assert client.get(f"/api/orders/{saved['order_id']}").status_code == 200


def load_lambda():
    spec = importlib.util.spec_from_file_location("order_processor", ROOT / "lambda" / "order_processor.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def stream_event(event_name="INSERT"):
    return {"Records": [{
        "eventName": event_name,
        "dynamodb": {"NewImage": {
            "order_id": {"S": "abcd1234-0000"},
            "total_inr": {"N": "1097"},
            "items": {"L": [{"M": {"product_id": {"S": "p-008"}, "qty": {"N": "2"}}}]},
        }},
    }]}


@mock_aws
def test_lambda_writes_receipt_notifies_and_emits_metric(monkeypatch, capsys):
    boto3.client("s3", region_name=REGION).create_bucket(
        Bucket="data", CreateBucketConfiguration={"LocationConstraint": REGION})
    topic = boto3.client("sns", region_name=REGION).create_topic(Name="alerts")["TopicArn"]
    monkeypatch.setenv("BUCKET", "data")
    monkeypatch.setenv("TOPIC", topic)
    assert load_lambda().handler(stream_event(), None) == {"processed": 1}
    body = boto3.client("s3", region_name=REGION).get_object(
        Bucket="data", Key="receipts/abcd1234-0000.json")["Body"].read()
    receipt = json.loads(body)
    assert receipt["total_inr"] == 1097 and receipt["items"][0]["qty"] == 2
    metric_line = [json.loads(line) for line in capsys.readouterr().out.splitlines() if "_aws" in line][0]
    assert metric_line["OrdersPlaced"] == 1 and metric_line["OrderValueINR"] == 1097
    assert metric_line["_aws"]["CloudWatchMetrics"][0]["Namespace"] == "ShopEasy"


@mock_aws
def test_lambda_ignores_non_insert_events(monkeypatch):
    monkeypatch.setenv("BUCKET", "data")
    monkeypatch.setenv("TOPIC", "arn:aws:sns:ap-southeast-2:123456789012:none")
    assert load_lambda().handler(stream_event("MODIFY"), None) == {"processed": 0}
