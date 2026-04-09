# QR Code Generator

Generates QR codes from URLs with optional logo overlay. Two interfaces: CLI for local use, and a FastAPI web app deployed to AWS Lambda via CDK. QR codes generated via the web app act as redirect proxies — they point to a `/redirect` endpoint which 302s to the actual destination, enabling scan tracking.

## Commands

- `python main.py -u <url> -d <filename> [-l <logo>]` — generate a QR code locally (saves to `qrs/`)
- `pip install -r requirements.txt` — install dependencies
- `npx aws-cdk deploy QrCodeStack` — deploy to AWS
- `npx aws-cdk destroy QrCodeStack` — tear down

## Structure

- `generate_qr.py` — core QR generation logic (shared by CLI and web app)
- `main.py` — CLI entry point
- `app.py` — FastAPI web app (Lambda handler via Mangum)
- `qr_code_stack.py` — CDK stack (Lambda, API Gateway, S3)
- `cdk_app.py` — CDK app entry point
- `Dockerfile` — Lambda container image (Python 3.12)

## Architecture

- QR generation uses `qrcode` + `Pillow`, returns JPEG bytes
- Web app receives URL + optional logo via multipart form POST to `/generate`, stores result in S3, returns public URL
- QR codes encode a redirect URL (`/redirect?qr=<uuid>`) instead of the raw destination. The `/redirect` endpoint looks up the destination in DynamoDB and returns a 302.
- Scan tracking: each redirect atomically increments a `hit_count` in DynamoDB and emits a structured CloudWatch log (`event: qr_redirect`). Use Logs Insights to query scan patterns.
- Lambda uses Docker image deployment; architecture auto-detected (ARM64/x86)
- S3 bucket has public read access for serving generated QR codes
- DynamoDB table stores QR code records (`id`, `destination_url`, `hit_count`), PAY_PER_REQUEST billing

## Prerequisites

- Python 3.12+, Docker, Node.js (for CDK), AWS CLI configured
