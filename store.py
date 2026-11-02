"""Data access for ShopEasy.

DynamoStore is used on AWS (products + orders in DynamoDB, images in S3).
MemoryStore is used for local runs and unit tests when no AWS settings exist.
"""
import os
from decimal import Decimal

from catalog import PRODUCTS


def plain(value):
    """DynamoDB returns numbers as Decimal; every number we store is a whole number,
    so turn them into int to keep the JSON API identical to the in-memory store."""
    if isinstance(value, Decimal):
        return int(value)
    if isinstance(value, list):
        return [plain(v) for v in value]
    if isinstance(value, dict):
        return {k: plain(v) for k, v in value.items()}
    return value


class MemoryStore:
    def __init__(self):
        self.products = {p["product_id"]: dict(p) for p in PRODUCTS}
        self.orders = {}

    def list_products(self, category=None):
        items = sorted(self.products.values(), key=lambda p: p["product_id"])
        return [p for p in items if not category or p["category"] == category]

    def get_product(self, product_id):
        return self.products.get(product_id)

    def put_order(self, order):
        self.orders[order["order_id"]] = order

    def get_order(self, order_id):
        return self.orders.get(order_id)

    def image_url(self, product):
        return None


class DynamoStore:
    def __init__(self, products_table, orders_table, bucket, region):
        import boto3
        from botocore.config import Config

        ddb = boto3.resource("dynamodb", region_name=region)
        self.products = ddb.Table(products_table)
        self.orders = ddb.Table(orders_table)
        self.bucket = bucket
        self.s3 = boto3.client("s3", region_name=region, config=Config(signature_version="s3v4"))

    def list_products(self, category=None):
        resp = self.products.scan()
        items = resp.get("Items", [])
        while "LastEvaluatedKey" in resp:
            resp = self.products.scan(ExclusiveStartKey=resp["LastEvaluatedKey"])
            items.extend(resp.get("Items", []))
        items = [plain(p) for p in items]
        items.sort(key=lambda p: p["product_id"])
        return [p for p in items if not category or p["category"] == category]

    def get_product(self, product_id):
        return plain(self.products.get_item(Key={"product_id": product_id}).get("Item"))

    def put_order(self, order):
        self.orders.put_item(Item=order)

    def get_order(self, order_id):
        return plain(self.orders.get_item(Key={"order_id": order_id}).get("Item"))

    def image_url(self, product):
        key = product.get("image_key")
        if not key or not self.bucket:
            return None
        return self.s3.generate_presigned_url(
            "get_object", Params={"Bucket": self.bucket, "Key": key}, ExpiresIn=3600
        )


def store_from_env():
    table = os.environ.get("PRODUCTS_TABLE")
    if not table:
        return MemoryStore()
    return DynamoStore(
        products_table=table,
        orders_table=os.environ["ORDERS_TABLE"],
        bucket=os.environ.get("DATA_BUCKET"),
        region=os.environ.get("AWS_REGION", "ap-southeast-2"),
    )
