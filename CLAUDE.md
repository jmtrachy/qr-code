# QR Code Generator

Generates QR codes from URLs with optional logo overlay. Two interfaces: CLI for local use, and a FastAPI web app deployed to AWS Lambda via CDK.

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
- Lambda uses Docker image deployment; architecture auto-detected (ARM64/x86)
- S3 bucket has public read access for serving generated QR codes

## Prerequisites

- Python 3.12+, Docker, Node.js (for CDK), AWS CLI configured
