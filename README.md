# ShopEasy: Cloud DevOps Capstone (Experiment 8)

**Business problem:** A small online retailer runs its store on one physical server in a back office. It has no automated releases, no monitoring, no audit trail and no way to handle sale-day traffic. ShopEasy moves it to AWS with a containerised app, automated CI/CD, IaC, monitoring, auditing and hardened access.

## Architecture

```
Developer -> GitHub (main) -> GitHub Actions
                               |- CI: pytest + docker build
                               |- CD: push image to ECR (tag = commit SHA)
                                      -> new ECS task definition -> rolling deploy
Users -> ALB (HTTP :80, public subnets, AlbSG)
          -> ECS Fargate tasks x2-4 (TaskSG: only ALB can reach :5000)
             -> logs -> CloudWatch Logs (/ecs/shopeasy)
CloudWatch: metrics + dashboard + alarms -> SNS email
CloudTrail -> encrypted private S3 bucket (log-file validation on)
CloudFormation (infra/network-ecs.yaml) defines all of it; AWS CLI scripts drive it
```

## Technology selection

| Requirement | Technology | Justification |
|---|---|---|
| Virtualization | AWS (Xen/Nitro hypervisor) VPC, Fargate | Replaces the physical server; no hardware, rack or datacentre to run; capacity on demand |
| Cloud / Compute | ECS on Fargate | No servers to patch; pay per task; autoscaling |
| Networking | VPC, 2 public subnets in 2 AZs, IGW, ALB, security groups | Network virtualization; multi-AZ availability; SG chaining limits exposure |
| Storage / DB | ECR (images), S3 (audit logs), no database yet (prototype) | Prototype keeps scope small; RDS/DynamoDB listed as future work |
| Containerization | Docker + ECR + ECS Fargate | Same image from laptop to prod; scan-on-push |
| Source control | GitHub | Free, integrates with Actions |
| CI | GitHub Actions (pytest, docker build) | Free tier, YAML in repo |
| CD | GitHub Actions + ECS rolling update, circuit-breaker rollback | Automatic deploy and auto-rollback on failure |
| Monitoring | CloudWatch metrics, Container Insights, dashboard, alarms + SNS | Native, no agents |
| Logging | CloudWatch Logs via awslogs driver | Centralised container logs |
| Auditing | CloudTrail to S3 | Records every API call (who/what/when) |
| Security / Hardening | Non-root container, SG-to-SG rules, IAM least privilege roles, ECR scan, S3 public-access block + encryption | Addresses access control, network exposure, permissions |
| IaC | CloudFormation | Repeatable, versioned, one-command create/delete |
| AWS CLI | deploy.sh, cli-evidence.sh, teardown.sh | Scripted management and evidence |
| Resource management | Autoscaling (CPU 60%), ECR lifecycle rule, log retention 7 days, teardown script | Controls cost and utilisation |

## Deploy (about 30–40 minutes)

**Prerequisites:** AWS account, `aws configure` done (IAM user with admin for the demo), Docker running, Git. Use region `ap-southeast-2` (change `AWS_REGION` if you prefer another).

```bash
chmod +x scripts/*.sh
./scripts/deploy.sh your-email@example.com
```

1. Confirm the SNS subscription email that AWS sends you (needed for alarm emails).
2. The script ends with the app URL; open `<URL>/` and `<URL>/health`.

### Set up CI/CD
```bash
git init && git add . && git commit -m "initial"
# create an empty GitHub repo, then:
git remote add origin https://github.com/<you>/shopeasy.git
git branch -M main && git push -u origin main
```
In GitHub: Settings > Secrets and variables > Actions, add `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` (for a real project use a dedicated IAM user limited to ECR + ECS, or OIDC).

### The "meaningful change" demo (required by section 9)
Edit `app.py`: change the welcome text to `"Welcome to ShopEasy v3"` and push to `main`. Screenshot the Actions run (tests, build, deploy), then open `<URL>/` showing v3 (before it showed v2).

### Demonstrate scalability / availability / monitoring
```bash
# load: run from your laptop for a minute or two
for i in $(seq 1 3000); do curl -s $URL/ >/dev/null & done
# availability: stop one task and watch ECS replace it
aws ecs list-tasks --cluster shopeasy-cluster --query "taskArns[0]" --output text
aws ecs stop-task --cluster shopeasy-cluster --task <arn>
```
Then run `./scripts/cli-evidence.sh` and screenshot the output.

### After the demo
`./scripts/teardown.sh` deletes everything (ALB and Fargate cost money while running; roughly a couple of dollars per day).

## Evidence checklist (screenshots)

| Concept | Screenshot |
|---|---|
| Virtual data centre | VPC console: VPC, subnets, route table, IGW |
| Cloud deployment | App URL in browser showing `/` and `/health` |
| Containerisation | ECR repo with images + scan result; ECS cluster with running tasks |
| IaC | CloudFormation stack, Resources tab, status CREATE_COMPLETE |
| CI/CD | GitHub Actions green run, with before/after of the app change |
| Monitoring | CloudWatch dashboard, alarms list, Container Insights |
| Logging | CloudWatch Logs `/ecs/shopeasy` showing Flask request lines (GET /health, GET /) |
| Auditing | CloudTrail event history (e.g. UpdateService), trail status |
| Security | Security group inbound rules (TaskSG only from AlbSG), IAM roles, S3 block public access |
| AWS CLI | Output of `cli-evidence.sh` |
| Scalability | ECS service autoscaling policy; task count rising under load |
| Availability | Task stopped and replaced; targets in 2 AZs on the target group |

## Test cases (fill in Actual/Status when you run them)

| Test case | Expected | Actual | Status |
|---|---|---|---|
| GET /health | 200 `OK` | | |
| GET / | 200 `Welcome to ShopEasy v2` | | |
| Push code with failing test | Pipeline stops at CI, no deploy | | |
| Push valid change | Deployed, new version at `/` | | |
| Stop one task | ECS starts replacement, app stays up | | |
| Load test | Autoscaling adds tasks, or CPU alarm fires | | |
| Direct access to task :5000 from internet | Blocked (SG) | | |
| Stack delete and re-create | Identical environment (repeatability) | | |

## Report notes (sections 15 and cost)

- **Virtualization / footprint:** one physical server and its power, cooling and maintenance replaced by virtualised cloud resources. Server virtualization = Fargate/EC2 hypervisor; network virtualization = VPC, subnets, SGs; **desktop virtualization is not implemented** (the retailer's staff only use a browser). It could be added with Amazon WorkSpaces for back-office staff.
- **Cost factors:** Fargate vCPU/memory hours, ALB hours, data transfer, CloudWatch logs/alarms, ECR storage, CloudTrail (additional trails beyond the first free one). **Existing approach:** upfront hardware, manual deploys, no failover. **Assumptions:** low traffic, 2 small tasks, one region.
- **Benefits:** automated releases, auto-recovery, elastic scaling, audit trail, repeatable environments, less operational effort.
- **Limitations:** HTTP only (no HTTPS/domain), no database or product catalogue yet (the app is a minimal Flask service), public subnets for tasks, single region, long-lived access keys in GitHub secrets.
- **Future enhancements:** HTTPS with ACM + Route 53, RDS/DynamoDB, private subnets + NAT/VPC endpoints, WAF, OIDC for GitHub, blue/green with CodeDeploy, WorkSpaces.
