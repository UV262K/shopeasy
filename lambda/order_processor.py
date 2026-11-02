import json, os, time
import boto3
from boto3.dynamodb.types import TypeDeserializer

s3 = boto3.client("s3")
sns = boto3.client("sns")
deser = TypeDeserializer()


def handler(event, context):
    done = 0
    for rec in event["Records"]:
        if rec["eventName"] != "INSERT":
            continue
        o = {k: deser.deserialize(v) for k, v in rec["dynamodb"]["NewImage"].items()}
        oid = o["order_id"]
        s3.put_object(
            Bucket=os.environ["BUCKET"],
            Key=f"receipts/{oid}.json",
            Body=json.dumps(o, default=int, indent=2),
            ContentType="application/json",
            ServerSideEncryption="AES256",
        )
        sns.publish(
            TopicArn=os.environ["TOPIC"],
            Subject=f"ShopEasy order {oid[:8]}",
            Message=f"Order {oid} placed. Items: {len(o['items'])}. Total: INR {o['total_inr']}.",
        )
        # CloudWatch Embedded Metric Format: this log line becomes custom metrics.
        print(json.dumps({
            "_aws": {
                "Timestamp": int(time.time() * 1000),
                "CloudWatchMetrics": [{
                    "Namespace": "ShopEasy",
                    "Dimensions": [[]],
                    "Metrics": [
                        {"Name": "OrdersPlaced", "Unit": "Count"},
                        {"Name": "OrderValueINR", "Unit": "None"},
                    ],
                }],
            },
            "OrdersPlaced": 1,
            "OrderValueINR": int(o["total_inr"]),
            "order_id": oid,
        }))
        done += 1
    return {"processed": done}
