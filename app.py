import json
import os
import uuid

import boto3
from fastapi import FastAPI, File, Form, UploadFile
from mangum import Mangum

from generate_qr import generate_qr

app = FastAPI()

S3_BUCKET = os.environ["QR_S3_BUCKET"]
CUSTOM_DOMAIN = os.environ.get("CUSTOM_DOMAIN", "")
s3 = boto3.client("s3")


@app.post("/generate")
async def generate(
    qr_info: str = Form(...),
    logo: UploadFile | None = File(None),
):
    info = json.loads(qr_info)
    url = info["url"]
    destination_file = info.get("destination_file", f"{uuid.uuid4()}.jpg")

    logo_bytes = None
    if logo:
        logo_bytes = await logo.read()

    image_bytes = generate_qr(url, logo_bytes)

    s3_key = f"qrs/{destination_file}"
    s3.put_object(
        Bucket=S3_BUCKET,
        Key=s3_key,
        Body=image_bytes,
        ContentType="image/jpeg",
    )

    if CUSTOM_DOMAIN:
        file_url = f"https://{CUSTOM_DOMAIN}/{s3_key}"
    else:
        file_url = f"https://{S3_BUCKET}.s3.amazonaws.com/{s3_key}"
    return {"generated_file_location": file_url}


handler = Mangum(app, lifespan="off")
