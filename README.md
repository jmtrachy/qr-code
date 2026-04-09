# QR Code Generator

Generate QR codes that track scans via a redirect proxy. Hosted at `https://qrcode.jamestrachy.com`.

## Generate a QR code

```bash
curl -X POST https://qrcode.jamestrachy.com/generate \
  -F 'qr_info={"url": "https://www.google.com"}'
```

With a custom filename:

```bash
curl -X POST https://qrcode.jamestrachy.com/generate \
  -F 'qr_info={"url": "https://www.google.com", "destination_file": "my-qr.jpg"}'
```

With a logo overlay:

```bash
curl -X POST https://qrcode.jamestrachy.com/generate \
  -F 'qr_info={"url": "https://www.google.com"}' \
  -F 'logo=@/path/to/logo.png'
```

Response:

```json
{
  "generated_file_location": "https://qrcode.jamestrachy.com/qrs/abc123.jpg",
  "qr_id": "abc123-..."
}
```

## Test the redirect

```bash
curl -v "https://qrcode.jamestrachy.com/redirect?qr=<qr_id>"
```

This returns a 302 redirect to the destination URL and increments the scan counter.

## Check scan count

```bash
aws dynamodb get-item \
  --table-name <table-name> \
  --key '{"id": {"S": "<qr_id>"}}' \
  --query 'Item.hit_count.N'
```

Or query CloudWatch Logs Insights against the Lambda's log group:

```
fields @timestamp, qr_id, destination_url
| filter event = "qr_redirect"
| stats count() by qr_id
```
