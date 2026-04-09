import json
import logging
import os
import uuid

import boto3
from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import RedirectResponse
from mangum import Mangum

from generate_qr import generate_qr

logger = logging.getLogger()
logger.setLevel(logging.INFO)

app = FastAPI()

S3_BUCKET = os.environ["QR_S3_BUCKET"]
DYNAMO_TABLE = os.environ["QR_DYNAMO_TABLE"]
CUSTOM_DOMAIN = os.environ.get("CUSTOM_DOMAIN", "")
s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(DYNAMO_TABLE)


@app.post("/generate")
async def generate(
    qr_info: str = Form(...),
    logo: UploadFile | None = File(None),
):
    info = json.loads(qr_info)
    url = info["url"]
    qr_id = str(uuid.uuid4())
    destination_file = info.get("destination_file", f"{qr_id}.jpg")

    table.put_item(
        Item={
            "id": qr_id,
            "destination_url": url,
            "hit_count": 0,
        }
    )

    redirect_url = f"https://{CUSTOM_DOMAIN}/redirect?qr={qr_id}" if CUSTOM_DOMAIN else f"/redirect?qr={qr_id}"

    logo_bytes = None
    if logo:
        logo_bytes = await logo.read()

    image_bytes = generate_qr(redirect_url, logo_bytes)

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
    return {"generated_file_location": file_url, "qr_id": qr_id}


@app.get("/redirect")
async def redirect(qr: str = Query(...)):
    result = table.get_item(Key={"id": qr})
    item = result.get("Item")

    if not item:
        raise HTTPException(status_code=404, detail="QR code not found")

    destination_url = item["destination_url"]

    table.update_item(
        Key={"id": qr},
        UpdateExpression="ADD hit_count :inc",
        ExpressionAttributeValues={":inc": 1},
    )

    logger.info(json.dumps({
        "event": "qr_redirect",
        "qr_id": qr,
        "destination_url": destination_url,
    }))

    return RedirectResponse(url=destination_url, status_code=302)


handler = Mangum(app, lifespan="off")
