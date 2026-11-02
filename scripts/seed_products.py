#!/usr/bin/env python3
"""Seed DynamoDB product rows and generate simple SVG product illustrations in S3."""
import os
from catalog import CATEGORY_COLOURS, PRODUCTS


def main():
    import boto3

    region = os.environ.get("AWS_REGION", "ap-southeast-2")
    table_name = os.environ["PRODUCTS_TABLE"]
    bucket = os.environ["DATA_BUCKET"]
    table = boto3.resource("dynamodb", region_name=region).Table(table_name)
    s3 = boto3.client("s3", region_name=region)

    with table.batch_writer() as batch:
        for product in PRODUCTS:
            p = dict(product)
            p["image_key"] = f"images/{p['product_id']}.svg"
            batch.put_item(Item=p)
            color = CATEGORY_COLOURS[p["category"]]
            label = p["name"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="640" height="480" viewBox="0 0 640 480">
<rect width="640" height="480" rx="36" fill="#101827"/>
<circle cx="500" cy="90" r="170" fill="{color}" opacity=".22"/>
<rect x="44" y="44" width="552" height="392" rx="26" fill="none" stroke="{color}" stroke-opacity=".7" stroke-width="3"/>
<text x="320" y="220" text-anchor="middle" fill="{color}" font-family="Arial" font-size="23">{label}</text>
<text x="320" y="270" text-anchor="middle" fill="#ffffff" font-family="Arial" font-size="16">SHOPEASY PRODUCT</text>
</svg>'''
            s3.put_object(
                Bucket=bucket, Key=p["image_key"], Body=svg.encode(),
                ContentType="image/svg+xml", ServerSideEncryption="AES256",
            )
    print(f"Seeded {len(PRODUCTS)} products and images")


if __name__ == "__main__":
    main()
