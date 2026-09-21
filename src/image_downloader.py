import os
import re
import time
import hashlib
import requests

from PIL import Image


def create_safe_folder_name(food_name):
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', food_name)
    return safe_name.strip()


def validate_image(file_path, min_width=300, min_height=200):
    try:
        with Image.open(file_path) as image:

            width, height = image.size
            image_format = image.format

            allowed_formats = {
                "JPEG",
                "PNG",
                "WEBP"
            }

            if image_format not in allowed_formats:
                return {
                    "valid": False,
                    "reason": f"Unsupported format: {image_format}",
                    "width": width,
                    "height": height,
                    "format": image_format
                }

            if width < min_width or height < min_height:
                return {
                    "valid": False,
                    "reason": f"Low resolution: {width}x{height}",
                    "width": width,
                    "height": height,
                    "format": image_format
                }

            image.verify()

        return {
            "valid": True,
            "reason": "Valid image",
            "width": width,
            "height": height,
            "format": image_format
        }

    except Exception as error:

        return {
            "valid": False,
            "reason": f"Invalid image: {error}",
            "width": None,
            "height": None,
            "format": None
        }


def get_file_extension(image_format):

    extension_map = {
        "JPEG": ".jpg",
        "PNG": ".png",
        "WEBP": ".webp"
    }

    return extension_map.get(
        image_format,
        ".jpg"
    )


def calculate_file_hash(file_path):

    hash_object = hashlib.sha256()

    try:

        with open(file_path, "rb") as file:

            while True:

                chunk = file.read(8192)

                if not chunk:
                    break

                hash_object.update(chunk)

        return hash_object.hexdigest()

    except Exception:
        return None


def get_existing_image_hashes(folder):

    hashes = set()

    if not os.path.exists(folder):
        return hashes

    for filename in os.listdir(folder):

        file_path = os.path.join(
            folder,
            filename
        )

        if not os.path.isfile(file_path):
            continue

        if filename.endswith(
            (".jpg", ".jpeg", ".png", ".webp")
        ):

            file_hash = calculate_file_hash(
                file_path
            )

            if file_hash:
                hashes.add(file_hash)

    return hashes


def download_image(
    image_url,
    save_path,
    retries=3,
    existing_hashes=None
):

    if not image_url:

        print(
            "No image URL provided."
        )

        return False

    if existing_hashes is None:
        existing_hashes = set()

    for attempt in range(
        1,
        retries + 1
    ):

        temporary_path = (
            save_path + ".tmp"
        )

        try:

            print(
                f"Download attempt "
                f"{attempt}/{retries}"
            )

            response = requests.get(
                image_url,
                timeout=30,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 "
                        "(Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 "
                        "(KHTML, like Gecko) "
                        "Chrome/131.0 Safari/537.36"
                    )
                }
            )

            response.raise_for_status()

            content_type = response.headers.get(
                "Content-Type",
                ""
            ).lower()

            if not content_type.startswith("image/"):

                print(
                    f"Rejected: Content-Type = "
                    f"{content_type}"
                )

                continue

            if not response.content:

                print(
                    "Rejected: Empty response."
                )

                continue

            folder = os.path.dirname(
                save_path
            )

            if folder:
                os.makedirs(
                    folder,
                    exist_ok=True
                )

            with open(
                temporary_path,
                "wb"
            ) as file:

                file.write(
                    response.content
                )

            validation = validate_image(
                temporary_path
            )

            if not validation["valid"]:

                print(
                    "Validation failed: "
                    f"{validation['reason']}"
                )

                if os.path.exists(
                    temporary_path
                ):
                    os.remove(
                        temporary_path
                    )

                continue

            # --------------------------------------------
            # Duplicate detection
            # --------------------------------------------

            new_hash = calculate_file_hash(
                temporary_path
            )

            if (
                new_hash
                and new_hash in existing_hashes
            ):

                print(
                    "Duplicate image detected."
                )

                print(
                    "Skipping this image."
                )

                if os.path.exists(
                    temporary_path
                ):
                    os.remove(
                        temporary_path
                    )

                return False

            # --------------------------------------------
            # Determine actual extension
            # --------------------------------------------

            image_format = validation[
                "format"
            ]

            extension = get_file_extension(
                image_format
            )

            base_path = os.path.splitext(
                save_path
            )[0]

            final_path = (
                base_path + extension
            )

            # --------------------------------------------
            # Save valid image
            # --------------------------------------------

            os.replace(
                temporary_path,
                final_path
            )

            if new_hash:
                existing_hashes.add(
                    new_hash
                )

            print(
                f"Valid image: "
                f"{validation['width']}x"
                f"{validation['height']} "
                f"{validation['format']}"
            )

            print(
                f"Saved: {final_path}"
            )

            return True

        except requests.RequestException as error:

            print(
                f"HTTP error on attempt "
                f"{attempt}: {error}"
            )

            if os.path.exists(
                temporary_path
            ):
                os.remove(
                    temporary_path
                )

        except Exception as error:

            print(
                f"Unexpected error on attempt "
                f"{attempt}: {error}"
            )

            if os.path.exists(
                temporary_path
            ):
                os.remove(
                    temporary_path
                )

        if attempt < retries:

            print(
                "Retrying..."
            )

            time.sleep(2)

    print(
        "All download attempts failed."
    )

    return False