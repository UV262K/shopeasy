import pytest

from app import app
from decimal import Decimal

from store import MemoryStore, plain


@pytest.fixture
def client():
    app.config["STORE"] = MemoryStore()
    app.config["TESTING"] = True
    return app.test_client()


def order(client, **body):
    return client.post("/api/checkout", json=body)


def test_health():
    assert app.test_client().get("/health").status_code == 200


def test_home_page_renders(client):
    r = client.get("/")
    assert r.status_code == 200
    assert b"shopeasy" in r.data


def test_products_listed(client):
    items = client.get("/api/products").get_json()
    assert len(items) == 12
    assert {"product_id", "name", "category", "price_inr", "image_url"} <= set(items[0])


def test_products_filtered_by_category(client):
    items = client.get("/api/products?category=Audio").get_json()
    assert items and all(p["category"] == "Audio" for p in items)


def test_checkout_below_free_shipping_adds_fee(client):
    r = order(client, items=[{"product_id": "p-008", "qty": 2}])  # 2 x 499 = 998
    assert r.status_code == 201
    body = r.get_json()
    assert body["subtotal_inr"] == 998
    assert body["shipping_inr"] == 99
    assert body["total_inr"] == 1097
    assert body["status"] == "PLACED"


def test_checkout_free_shipping_at_threshold(client):
    r = order(client, items=[{"product_id": "p-003", "qty": 1}, {"product_id": "p-010", "qty": 3}])  # 1799+2997
    body = r.get_json()
    assert body["subtotal_inr"] == 4796
    assert body["shipping_inr"] == 0


def test_checkout_merges_duplicate_lines(client):
    r = order(client, items=[{"product_id": "p-008", "qty": 1}, {"product_id": "p-008", "qty": 2}])
    assert r.get_json()["items"][0]["qty"] == 3


def test_client_cannot_set_price(client):
    r = order(client, items=[{"product_id": "p-001", "qty": 1, "price_inr": 1}])
    assert r.get_json()["subtotal_inr"] == 2499


@pytest.mark.parametrize("body", [
    {},
    {"items": []},
    {"items": "p-001"},
    {"items": [{"product_id": "p-001", "qty": 0}]},
    {"items": [{"product_id": "p-001", "qty": 11}]},
    {"items": [{"product_id": "p-001", "qty": 1.5}]},
    {"items": [{"product_id": "p-001", "qty": True}]},
    {"items": [{"qty": 1}]},
    {"items": [{"product_id": "nope", "qty": 1}]},
    {"items": [{"product_id": "p-001", "qty": 1}], "customer_email": "not-an-email"},
])
def test_checkout_rejects_bad_input(client, body):
    assert order(client, **body).status_code == 400


def test_checkout_rejects_non_json(client):
    assert client.post("/api/checkout", data="hello").status_code == 400


def test_order_can_be_fetched_without_email(client):
    created = order(client, items=[{"product_id": "p-001", "qty": 1}], customer_email="a@b.com")
    assert "customer_email" not in created.get_json()
    fetched = client.get(f"/api/orders/{created.get_json()['order_id']}")
    assert fetched.status_code == 200
    assert "customer_email" not in fetched.get_json()


def test_unknown_order_is_404():
    client = app.test_client()
    client.application.config["STORE"] = MemoryStore()
    assert client.get("/api/orders/does-not-exist").status_code == 404


def test_database_failure_returns_503(client):
    class Broken(MemoryStore):
        def put_order(self, order):
            raise RuntimeError("db down")

    app.config["STORE"] = Broken()
    assert order(client, items=[{"product_id": "p-001", "qty": 1}]).status_code == 503


def test_plain_converts_dynamodb_decimals_to_int():
    raw = {"price_inr": Decimal("2499"), "items": [{"qty": Decimal("2"), "name": "x"}], "n": None}
    out = plain(raw)
    assert out == {"price_inr": 2499, "items": [{"qty": 2, "name": "x"}], "n": None}
    assert type(out["price_inr"]) is int and type(out["items"][0]["qty"]) is int
