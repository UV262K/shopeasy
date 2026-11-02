#!/usr/bin/env bash
# One-shot deploy using AWS CLI + CloudFormation.
# Usage: ./scripts/deploy.sh you@example.com
set -euo pipefail

EMAIL="${1:?usage: deploy.sh <alert-email>}"
REGION="${AWS_REGION:-ap-southeast-2}"
STACK="shopeasy"
TAG="v1"
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
REPO="$ACCOUNT.dkr.ecr.$REGION.amazonaws.com/shopeasy"
TEMPLATE="infra/network-ecs.yaml"

echo ">> 1. Validate template"
aws cloudformation validate-template --template-body "file://$TEMPLATE" --region "$REGION" >/dev/null

echo ">> 2. Create/update infrastructure with service initially at zero tasks"
aws cloudformation deploy --stack-name "$STACK" --template-file "$TEMPLATE" \
  --region "$REGION" --capabilities CAPABILITY_IAM \
  --parameter-overrides AlertEmail="$EMAIL" ImageTag="$TAG" DesiredCount=0

out() { aws cloudformation describe-stacks --stack-name "$STACK" --region "$REGION" \
  --query "Stacks[0].Outputs[?OutputKey=='$1'].OutputValue" --output text; }

echo ">> 3. Seed DynamoDB products and S3 images"
python3 -m pip install -q boto3
PRODUCTS_TABLE="$(out ProductsTableName)" DATA_BUCKET="$(out DataBucketName)" AWS_REGION="$REGION" \
  python3 scripts/seed_products.py

echo ">> 4. Sync Lambda code, build and push container image"
python3 scripts/sync_lambda.py
aws ecr get-login-password --region "$REGION" | docker login --username AWS --password-stdin "$ACCOUNT.dkr.ecr.$REGION.amazonaws.com"
docker build -f dockerfile -t "$REPO:$TAG" .
docker push "$REPO:$TAG"

echo ">> 5. Scale service to two tasks"
aws cloudformation deploy --stack-name "$STACK" --template-file "$TEMPLATE" \
  --region "$REGION" --capabilities CAPABILITY_IAM \
  --parameter-overrides AlertEmail="$EMAIL" ImageTag="$TAG" DesiredCount=2

echo ">> 6. Wait for service to stabilise"
aws ecs wait services-stable --cluster shopeasy-cluster --services shopeasy-service --region "$REGION"

URL=$(out AppUrl)
echo ">> DONE. App URL: $URL"
curl -fsS "$URL/health"; echo
echo ">> Products from DynamoDB:"
curl -fsS "$URL/api/products" | head -c 300; echo
echo ">> Next: ./scripts/demo-order.sh to place a test order and watch Lambda, S3 and CloudWatch react"
