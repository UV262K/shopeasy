# ShopEasy — Cloud DevOps Capstone

ShopEasy is a demo electronics storefront packaged as a Flask application and containerised for deployment to AWS ECS Fargate.

## Storefront features

- Responsive electronics storefront served at `/`
- Product catalogue API at `GET /api/products`
- Runtime information endpoint at `GET /api/info`
- Demo checkout endpoint at `POST /api/checkout`
- Health endpoint at `GET /health`
- Coupon code `EASY10`; free shipping for discounted subtotals of ₹4,000 or more

The product catalogue and checkout order counter are held in process memory. There is no persistent database or real payment processing; this is a demonstration application, not a production store.

## Architecture

GitHub Actions runs the Python tests and builds a Docker image. The deployment job is restricted to pushes on `main`, where it can push the image to ECR and update the ECS Fargate service. The existing CloudFormation template defines the VPC, load balancer, ECR, ECS, monitoring and CloudTrail resources.

## Run locally

```bash
python -m pip install -r requirements.txt
python - <<'PY'
import zipfile
with zipfile.ZipFile("storefront-source.zip") as archive:
    for name in ("app.py", "test_app.py", "static/index.html"):
        archive.extract(name, ".")
PY
python -m pytest -q
python app.py
```

Open `http://localhost:5000`.

To build the container:

```bash
docker build -t shopeasy:local .
docker run --rm -p 5000:5000 shopeasy:local
```

The Dockerfile expands the storefront source archive as part of the image build.

## AWS deployment and costs

The existing AWS deployment scripts and CloudFormation template are retained. The workflow deploys only from `main`; opening or updating a pull request runs CI but does not deploy. Do not merge to `main` until AWS credentials, resource names, region, task definition and deployment settings have been verified.

An Application Load Balancer and Fargate tasks can incur charges while running. Use the supplied teardown script when the demonstration environment is no longer needed. Store AWS credentials only as GitHub Actions secrets; never commit keys to the repository.
