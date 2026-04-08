import io

import qrcode
from PIL import Image


def generate_qr(url: str, logo_bytes: bytes | None = None) -> bytes:
    """Generate a QR code image and return it as JPEG bytes.

    Args:
        url: The URL to encode in the QR code.
        logo_bytes: Optional raw bytes of a logo image to embed in the center.

    Returns:
        JPEG image bytes of the generated QR code.
    """
    error_correction = (
        qrcode.constants.ERROR_CORRECT_H
        if logo_bytes
        else qrcode.constants.ERROR_CORRECT_M
    )

    qr = qrcode.QRCode(error_correction=error_correction, box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGBA")

    if logo_bytes:
        logo = Image.open(io.BytesIO(logo_bytes)).convert("RGBA")
        max_logo_size = img.size[0] // 4
        logo.thumbnail((max_logo_size, max_logo_size))
        logo_x = (img.size[0] - logo.size[0]) // 2
        logo_y = (img.size[1] - logo.size[1]) // 2
        img.paste(logo, (logo_x, logo_y), logo)

    # Convert RGBA to RGB for JPEG output
    rgb_img = Image.new("RGB", img.size, (255, 255, 255))
    rgb_img.paste(img, mask=img.split()[3])

    buf = io.BytesIO()
    rgb_img.save(buf, format="JPEG")
    return buf.getvalue()
