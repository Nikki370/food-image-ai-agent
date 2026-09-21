import os

from PIL import Image, ImageOps


# ============================================================
# CONFIGURATION
# ============================================================

TARGET_WIDTH = 1800
TARGET_HEIGHT = 1200

MAX_FILE_SIZE_MB = 10

JPEG_QUALITY = 95


# ============================================================
# PROCESS IMAGE
# ============================================================

def process_image(
    input_path,
    output_path,
    target_width=TARGET_WIDTH,
    target_height=TARGET_HEIGHT
):
    """
    Convert an image to exactly target_width x target_height
    while preserving the image's aspect ratio.

    The image is resized and center-cropped if necessary.
    """

    if not os.path.exists(input_path):
        raise FileNotFoundError(
            f"Input image not found: {input_path}"
        )

    try:

        # ----------------------------------------------------
        # Open image
        # ----------------------------------------------------

        with Image.open(input_path) as image:

            print(
                f"Original size: "
                f"{image.width}x{image.height}"
            )

            print(
                f"Original format: "
                f"{image.format}"
            )

            # ------------------------------------------------
            # Convert to RGB
            # ------------------------------------------------

            if image.mode != "RGB":
                image = image.convert("RGB")

            # ------------------------------------------------
            # Resize + center crop
            # ------------------------------------------------

            processed_image = ImageOps.fit(
                image,
                (
                    target_width,
                    target_height
                ),
                method=Image.Resampling.LANCZOS,
                centering=(0.5, 0.5)
            )

            print(
                f"Processed size: "
                f"{processed_image.width}x"
                f"{processed_image.height}"
            )

            # ------------------------------------------------
            # Create output folder
            # ------------------------------------------------

            output_folder = os.path.dirname(
                output_path
            )

            if output_folder:
                os.makedirs(
                    output_folder,
                    exist_ok=True
                )

            # ------------------------------------------------
            # Save as JPEG
            # ------------------------------------------------

            processed_image.save(
                output_path,
                format="JPEG",
                quality=JPEG_QUALITY,
                optimize=True
            )

        # ----------------------------------------------------
        # Check output file
        # ----------------------------------------------------

        if not os.path.exists(output_path):

            raise RuntimeError(
                "Processed image was not created."
            )

        file_size_bytes = os.path.getsize(
            output_path
        )

        file_size_mb = (
            file_size_bytes /
            (1024 * 1024)
        )

        print(
            f"Final file size: "
            f"{file_size_mb:.2f} MB"
        )

        # ----------------------------------------------------
        # Check size limit
        # ----------------------------------------------------

        if file_size_mb > MAX_FILE_SIZE_MB:

            raise RuntimeError(
                f"File size is "
                f"{file_size_mb:.2f} MB, "
                f"which exceeds the "
                f"{MAX_FILE_SIZE_MB} MB limit."
            )

        # ----------------------------------------------------
        # Verify final dimensions
        # ----------------------------------------------------

        with Image.open(output_path) as final_image:

            if (
                final_image.width != target_width
                or
                final_image.height != target_height
            ):

                raise RuntimeError(
                    "Final image dimensions "
                    "are incorrect."
                )

        print(
            "Image processing successful ✓"
        )

        return {
            "success": True,
            "output_path": output_path,
            "width": target_width,
            "height": target_height,
            "size_mb": round(
                file_size_mb,
                2
            )
        }

    except Exception as error:

        print(
            f"Image processing failed: "
            f"{error}"
        )

        return {
            "success": False,
            "output_path": None,
            "width": None,
            "height": None,
            "size_mb": None,
            "error": str(error)
        }