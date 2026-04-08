# QR Code Lambda - Setup & Deployment

## Prerequisites

- AWS CLI configured with credentials (`aws configure`)
- Docker running
- Node.js (for npx to run CDK)
- Python 3.12+

## Deploy

```bash
# Install all deps in your existing venv
source venv/bin/activate
pip install -r requirements.txt

# Bootstrap CDK (one-time per AWS account/region)
npx aws-cdk bootstrap

# Deploy
npx aws-cdk deploy QrCodeStack
```

Outputs:
- **FunctionUrl** - your endpoint
- **BucketName** - where QR codes are stored

## Test with curl

```bash
# With logo
curl -X POST <FunctionUrl>/generate \
  -F "logo=@/path/to/photo.jpg" \
  -F 'qr_info={"destination_file": "example_qr.jpg", "url": "https://www.google.com"};type=application/json'

# Without logo
curl -X POST <FunctionUrl>/generate \
  -F 'qr_info={"destination_file": "example_qr.jpg", "url": "https://www.google.com"};type=application/json'
```

Response: `{"generated_file_location": "https://<bucket>.s3.amazonaws.com/qr-codes/example_qr.jpg"}`

## Tear down

```bash
npx aws-cdk destroy QrCodeStack
```
