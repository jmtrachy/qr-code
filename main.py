import argparse
import os

from generate_qr import generate_qr


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

    logo_bytes = None
    if args.logo:
        with open(f"logos/{args.logo}", "rb") as f:
            logo_bytes = f.read()

    image_bytes = generate_qr(args.url, logo_bytes)

    file_path = os.path.join(output_dir, args.destination_file)
    with open(file_path, "wb") as f:
        f.write(image_bytes)

    print(f"QR code saved to: {os.path.abspath(file_path)}")


if __name__ == "__main__":
    main()
