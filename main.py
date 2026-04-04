import argparse
import os

import qrcode
from PIL import Image


def main():
    parser = argparse.ArgumentParser(description="Generate a QR code from a URL")
    parser.add_argument("-u", "--url", required=True, help="URL to embed in the QR code")
    parser.add_argument(
        "-d",
        "--destination_file",
        required=True,
        help="Filename for the generated QR code image",
    )
    parser.add_argument(
        "-l",
        "--logo",
        help="Path to a logo image to embed in the center of the QR code",
    )
    args = parser.parse_args()

    output_dir = "qrs"
    os.makedirs(output_dir, exist_ok=True)

    file_path = os.path.join(output_dir, args.destination_file)

    error_correction = qrcode.constants.ERROR_CORRECT_H if args.logo else qrcode.constants.ERROR_CORRECT_M

    qr = qrcode.QRCode(error_correction=error_correction, box_size=10, border=4)
    qr.add_data(args.url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGBA")

    if args.logo:
        logo = Image.open(f'logos/{args.logo}').convert("RGBA")
        max_logo_size = img.size[0] // 4
        logo.thumbnail((max_logo_size, max_logo_size))
        logo_x = (img.size[0] - logo.size[0]) // 2
        logo_y = (img.size[1] - logo.size[1]) // 2
        img.paste(logo, (logo_x, logo_y), logo)

    img.save(file_path)

    print(f"QR code saved to: {os.path.abspath(file_path)}")


if __name__ == "__main__":
    main()
