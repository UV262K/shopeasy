# ShopEasy AWS Upgrade Proposal

This branch documents the proposed data and monitoring architecture for the supplied `shopeasy-updated.zip` bundle. It does not claim that these resources have been provisioned or deployed.

## Proposed request flow

1. The Flask storefront serves the product catalogue and accepts checkout requests.
2. DynamoDB stores product records and orders. Checkout validates product IDs and quantities, then reads authoritative prices from the catalogue rather than trusting browser-supplied prices.
3. S3 stores product images and order-receipt JSON objects. Product images are private and delivered using short-lived presigned URLs.
4. A DynamoDB Streams INSERT event invokes the order-processing Lambda.
5. The Lambda writes a receipt to S3, publishes an SNS notification, and emits custom order metrics for CloudWatch.
6. CloudWatch collects container and Lambda logs/metrics, displays a dashboard, and triggers alarms for errors or unhealthy service signals.
7. CloudFormation defines the proposed infrastructure so it can be recreated consistently.

## Deployment separation

The existing GitHub Actions workflow handles application image CI/CD: test, build, push to ECR, update the ECS task definition, and verify application endpoints.

Infrastructure provisioning is a separate operation driven by the CloudFormation deployment script. A successful image pipeline alone does not provision DynamoDB, S3, Lambda, SNS, or the monitoring resources.

## Before merging or deploying

- Review the CloudFormation template and IAM permissions.
- Validate the template with `cfn-lint`.
- Install development dependencies and run the unit and AWS-mocked tests.
- Build the Docker image.
- Deploy into a non-production AWS account/stack and confirm the SNS subscription.
- Place a demo order and verify DynamoDB, the stream-triggered Lambda, S3 receipt, SNS notification, and CloudWatch metrics/logs.
- Confirm cleanup with the teardown script and inspect any retained resources.

## Status

This is a design/implementation handoff note only. The supplied ZIP still needs to be extracted into the repository, reviewed, tested in CI, and deployed to an AWS account before any of the proposed features can be described as operational.
