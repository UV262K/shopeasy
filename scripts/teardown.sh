#!/usr/bin/env bash
set -euo pipefail
REGION="${AWS_REGION:-ap-southeast-2}"
STACK="shopeasy"
echo "This deletes the ShopEasy CloudFormation stack and billable resources."
read -r -p "Type DELETE to continue: " CONFIRM
[[ "$CONFIRM" == "DELETE" ]] || { echo "Cancelled"; exit 1; }
aws cloudformation delete-stack --stack-name "$STACK" --region "$REGION"
aws cloudformation wait stack-delete-complete --stack-name "$STACK" --region "$REGION"
echo "Stack deleted. Check S3 buckets and ECR repositories for retained objects/images."
