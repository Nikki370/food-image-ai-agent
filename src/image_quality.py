import os
import cv2


def calculate_blur_score(image_path):
    """
    Calculate image sharpness using Laplacian variance.

    Higher score = sharper image
    Lower score = more blurry image
    """

    image = cv2.imread(image_path)

    if image is None:
        return 0

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    blur_score = cv2.Laplacian(
        gray,
        cv2.CV_64F
    ).var()

    return round(
        float(blur_score),
        2
    )


def calculate_resolution_score(
    width,
    height
):
    """
    Give a score based on image resolution.
    """

    pixels = width * height

    if pixels >= 1800 * 1200:
        return 100

    if pixels >= 1600 * 1000:
        return 90

    if pixels >= 1200 * 800:
        return 80

    if pixels >= 800 * 600:
        return 60

    if pixels >= 600 * 400:
        return 40

    return 20


def calculate_aspect_ratio_score(
    width,
    height
):
    """
    Compare image aspect ratio with
    the required 1800x1200 ratio.
    """

    if height == 0:
        return 0

    image_ratio = width / height

    target_ratio = 1800 / 1200

    difference = abs(
        image_ratio - target_ratio
    )

    if difference <= 0.10:
        return 100

    if difference <= 0.25:
        return 85

    if difference <= 0.45:
        return 70

    if difference <= 0.70:
        return 50

    return 30


def analyze_image(image_path):

    """
    Analyze one image and return
    quality metrics.
    """

    if not os.path.exists(image_path):

        return {
            "valid": False,
            "reason": "File not found"
        }

    image = cv2.imread(image_path)

    if image is None:

        return {
            "valid": False,
            "reason": "Unable to read image"
        }

    height, width = image.shape[:2]

    blur_score = calculate_blur_score(
        image_path
    )

    resolution_score = (
        calculate_resolution_score(
            width,
            height
        )
    )

    aspect_ratio_score = (
        calculate_aspect_ratio_score(
            width,
            height
        )
    )

    # --------------------------------------------------------
    # Blur score
    # --------------------------------------------------------

    if blur_score >= 500:
        blur_quality = 100

    elif blur_score >= 200:
        blur_quality = 85

    elif blur_score >= 100:
        blur_quality = 70

    elif blur_score >= 50:
        blur_quality = 50

    else:
        blur_quality = 20

    # --------------------------------------------------------
    # Overall quality score
    # --------------------------------------------------------

    quality_score = (
        resolution_score * 0.40
        + blur_quality * 0.40
        + aspect_ratio_score * 0.20
    )

    quality_score = round(
        quality_score,
        2
    )

    # --------------------------------------------------------
    # Quality decision
    # --------------------------------------------------------

    if quality_score >= 80:
        quality = "Excellent"

    elif quality_score >= 65:
        quality = "Good"

    elif quality_score >= 50:
        quality = "Average"

    else:
        quality = "Poor"

    return {

        "valid": True,

        "width": width,

        "height": height,

        "blur_score": blur_score,

        "resolution_score": resolution_score,

        "aspect_ratio_score": aspect_ratio_score,

        "quality_score": quality_score,

        "quality": quality
    }


def select_best_image(image_paths):
    """
    Analyze all downloaded images and
    return the highest-quality image.
    """

    best_image = None
    best_score = -1
    best_result = None

    for image_path in image_paths:

        result = analyze_image(image_path)

        if not result["valid"]:
            print(
                f"Skipping invalid image: "
                f"{image_path}"
            )
            continue

        score = result["quality_score"]

        print(
            f"{os.path.basename(image_path)} "
            f"→ Score: {score}"
        )

        if score > best_score:

            best_score = score
            best_image = image_path
            best_result = result

    if best_image is None:

        return {
            "success": False,
            "image_path": None,
            "quality": None
        }

    return {
        "success": True,
        "image_path": best_image,
        "quality": best_result
    }