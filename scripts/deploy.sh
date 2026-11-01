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

echo ">> 2. Create infrastructure (0 tasks, so the stack does not wait for an image)"
aws cloudformation deploy --stack-name "$STACK" --template-file "$TEMPLATE" \
  --region "$REGION" --capabilities CAPABILITY_IAM \
  --parameter-overrides AlertEmail="$EMAIL" ImageTag="$TAG" DesiredCount=0

echo ">> 3. Build and push container image"
aws ecr get-login-password --region "$REGION" | docker login --username AWS --password-stdin "$ACCOUNT.dkr.ecr.$REGION.amazonaws.com"
docker build -t "$REPO:$TAG" .
docker push "$REPO:$TAG"

echo ">> 4. Scale up: run 2 tasks"
aws cloudformation deploy --stack-name "$STACK" --template-file "$TEMPLATE" \
  --region "$REGION" --capabilities CAPABILITY_IAM \
  --parameter-overrides AlertEmail="$EMAIL" ImageTag="$TAG" DesiredCount=2

echo ">> 5. Wait for service to stabilise"
aws ecs wait services-stable --cluster shopeasy-cluster --services shopeasy-service --region "$REGION"

URL=$(aws cloudformation describe-stacks --stack-name "$STACK" --region "$REGION" \
  --query "Stacks[0].Outputs[?OutputKey=='AppUrl'].OutputValue" --output text)
echo ">> DONE. App URL: $URL"
curl -s "$URL/health"; echo
