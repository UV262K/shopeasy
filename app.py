import datetime
import logging
import uuid

from flask import Flask, jsonify, render_template, request

from store import store_from_env

VERSION = "v4"
FREE_SHIPPING_FROM_INR = 4000
SHIPPING_INR = 99
MAX_LINES = 20
MAX_QTY = 10

app = Flask(__name__)

# Under gunicorn, send Flask logs to the same stream so they reach CloudWatch Logs.
if __name__ != "__main__":
    _gunicorn = logging.getLogger("gunicorn.error")
    if _gunicorn.handlers:
        app.logger.handlers = _gunicorn.handlers
        app.logger.setLevel(_gunicorn.level)


def get_store():
    if "STORE" not in app.config:
        app.config["STORE"] = store_from_env()
    return app.config["STORE"]


@app.route("/")
def home():
    return render_template("index.html", version=VERSION)


@app.route("/health")
def health():
    return "OK", 200


@app.route("/api/products")
def products():
    store = get_store()
    try:
        items = store.list_products(request.args.get("category"))
    except Exception:
        app.logger.exception("products_unavailable")
        return jsonify(error="catalogue unavailable"), 503
    return jsonify([{**p, "image_url": store.image_url(p)} for p in items])


def _parse_lines(data):
    """Validate the cart. Returns (lines, error)."""
    raw = data.get("items")
    if not isinstance(raw, list) or not raw:
        return None, "items must be a non-empty list"
    if len(raw) > MAX_LINES:
        return None, f"at most {MAX_LINES} different products per order"
    merged = {}
    for line in raw:
        if not isinstance(line, dict):
            return None, "each item must be an object"
        pid, qty = line.get("product_id"), line.get("qty")
        if not isinstance(pid, str) or not pid:
            return None, "product_id is required"
        if isinstance(qty, bool) or not isinstance(qty, int) or not 1 <= qty <= MAX_QTY:
            return None, f"qty must be a whole number from 1 to {MAX_QTY}"
        merged[pid] = merged.get(pid, 0) + qty
    if any(q > MAX_QTY for q in merged.values()):
        return None, f"qty per product is limited to {MAX_QTY}"
    return merged, None


@app.route("/api/checkout", methods=["POST"])
def checkout():
    data = request.get_json(silent=True) or {}
    merged, error = _parse_lines(data)
    if error:
        return jsonify(error=error), 400

    email = data.get("customer_email")
    if email is not None and (not isinstance(email, str) or "@" not in email or len(email) > 120):
        return jsonify(error="customer_email looks invalid"), 400

    store = get_store()
    try:
        lines, subtotal = [], 0
        for pid, qty in merged.items():
            product = store.get_product(pid)
            if not product:
                return jsonify(error=f"unknown product {pid}"), 400
            price = int(product["price_inr"])  # always trust the database price, never the client
            lines.append({"product_id": pid, "name": product["name"], "qty": qty, "price_inr": price})
            subtotal += price * qty
        shipping = 0 if subtotal >= FREE_SHIPPING_FROM_INR else SHIPPING_INR
        order = {
            "order_id": str(uuid.uuid4()),
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
            "status": "PLACED",
            "items": lines,
            "subtotal_inr": subtotal,
            "shipping_inr": shipping,
            "total_inr": subtotal + shipping,
        }
        if email:
            order["customer_email"] = email
        store.put_order(order)
    except Exception:
        app.logger.exception("checkout_failed")
        return jsonify(error="could not place the order, please try again"), 503

    app.logger.info("order_created order_id=%s total_inr=%s lines=%s",
                    order["order_id"], order["total_inr"], len(lines))
    return jsonify({k: v for k, v in order.items() if k != "customer_email"}), 201


@app.route("/api/orders/<order_id>")
def order(order_id):
    try:
        found = get_store().get_order(order_id)
    except Exception:
        app.logger.exception("order_lookup_failed")
        return jsonify(error="order lookup unavailable"), 503
    if not found:
        return jsonify(error="order not found"), 404
    return jsonify({k: v for k, v in found.items() if k != "customer_email"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
