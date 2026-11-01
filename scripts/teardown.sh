#!/usr/bin/env bash
# Delete everything after your demo to avoid charges (ALB + Fargate cost money).
set -euo pipefail
REGION="${AWS_REGION:-ap-southeast-2}"
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
aws ecr batch-delete-image --repository-name shopeasy --region "$REGION" \
  --image-ids "$(aws ecr list-images --repository-name shopeasy --region "$REGION" --query 'imageIds[*]' --output json)" || true
BUCKET=$(aws cloudformation describe-stack-resource --stack-name shopeasy --logical-resource-id TrailBucket --region "$REGION" --query StackResourceDetail.PhysicalResourceId --output text)
aws s3 rm "s3://$BUCKET" --recursive || true
aws cloudformation delete-stack --stack-name shopeasy --region "$REGION"
aws cloudformation wait stack-delete-complete --stack-name shopeasy --region "$REGION"
echo "Stack deleted."
