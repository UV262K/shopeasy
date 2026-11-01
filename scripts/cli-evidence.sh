#!/usr/bin/env bash
# AWS CLI commands to screenshot as evidence (resource management, logging, auditing, security).
REGION="${AWS_REGION:-ap-southeast-2}"

echo "== Stack status ==";            aws cloudformation describe-stacks --stack-name shopeasy --region $REGION --query "Stacks[0].StackStatus"
echo "== Stack resources ==";         aws cloudformation list-stack-resources --stack-name shopeasy --region $REGION --output table
echo "== ECS service ==";             aws ecs describe-services --cluster shopeasy-cluster --services shopeasy-service --region $REGION --query "services[0].{status:status,desired:desiredCount,running:runningCount,taskDef:taskDefinition}"
echo "== ECR images + scan ==";       aws ecr describe-images --repository-name shopeasy --region $REGION --query "imageDetails[].{tags:imageTags,pushed:imagePushedAt,scan:imageScanStatus.status}"
echo "== Alarms ==";                  aws cloudwatch describe-alarms --alarm-name-prefix shopeasy --region $REGION --query "MetricAlarms[].{name:AlarmName,state:StateValue}" --output table
echo "== Recent app logs ==";         aws logs tail /ecs/shopeasy --since 15m --region $REGION | head -20
echo "== CloudTrail (who did what) =="; aws cloudtrail lookup-events --max-results 10 --region $REGION --query "Events[].{time:EventTime,event:EventName,user:Username}" --output table
echo "== Trail status ==";            aws cloudtrail get-trail-status --name shopeasy-audit-trail --region $REGION --query "{logging:IsLogging}"
echo "== Autoscaling ==";             aws application-autoscaling describe-scalable-targets --service-namespace ecs --region $REGION --query "ScalableTargets[].{min:MinCapacity,max:MaxCapacity}"
echo "== Security group rules ==";    aws ec2 describe-security-groups --filters Name=group-description,Values="Allow*" --region $REGION --query "SecurityGroups[].{desc:Description,ingress:IpPermissions[].{port:FromPort,src:IpRanges[].CidrIp,sg:UserIdGroupPairs[].GroupId}}"
