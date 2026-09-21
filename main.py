import os
import csv

from src.excel_reader import read_food_items
from src.image_search import search_images

from src.image_downloader import (
    download_image,
    create_safe_folder_name,
    get_existing_image_hashes
)

from src.image_quality import analyze_image

from src.image_processor import process_image
from src.food_ai import check_food_relevance
from src.google_drive import authenticate_google_drive, create_drive_folder, upload_file_to_drive


# ============================================================
# CONFIGURATION
# ============================================================

EXCEL_FILE = "data/food_items.xlsx"

DOWNLOAD_FOLDER = "downloads"

PROCESSED_FOLDER = "processed"

REPORT_FOLDER = "reports"
REPORT_FILE = os.path.join(
    REPORT_FOLDER,
    "processing_report.csv"
)

# Google Drive destination folder
GOOGLE_DRIVE_FOLDER_NAME = "Food Image AI Agent"
DRIVE_FOLDER_ID_FILE = "drive_folder_id.txt"
CHECKPOINT_FILE = "processed_items.txt"

# Number of image candidates to search for each food item
NUM_RESULTS = 3

# Keep True while testing
TEST_MODE = True

# Number of food items to process during testing
TEST_ITEMS = 10

# Minimum AI confidence required to accept an image
MIN_AI_CONFIDENCE = 70

# Resume processing of already downloaded images
RESUME_MODE = False

#=====================================================================
# get the Google Drive folder
# ==================================================================== 
def get_or_create_drive_folder(drive_service):
    if os.path.exists(DRIVE_FOLDER_ID_FILE):
        with open(DRIVE_FOLDER_ID_FILE, "r") as f:
            folder_id = f.read().strip()

        if folder_id:
            try:
                drive_service.files().get(
                    fileId=folder_id,
                    fields="id,name"
                ).execute()

                print(f"Using existing Drive folder: {GOOGLE_DRIVE_FOLDER_NAME}")
                return folder_id

            except Exception:
                print("Saved Drive folder not accessible. Creating a new one...")

    folder_id = create_drive_folder(
        drive_service,
        GOOGLE_DRIVE_FOLDER_NAME
    )

    with open(DRIVE_FOLDER_ID_FILE, "w") as f:
        f.write(folder_id)

    print(f"Created Drive folder: {GOOGLE_DRIVE_FOLDER_NAME}")
    return folder_id


# ============================================================
# PROCESSING REPORT
# ============================================================

def save_processing_report(result):

    os.makedirs(REPORT_FOLDER, exist_ok=True)

    file_exists = os.path.exists(REPORT_FILE)

    fieldnames = [
        "food_item",
        "found_images",
        "downloaded_images",
        "selected_image",
        "quality_score",
        "ai_food_match",
        "ai_confidence",
        "menu_suitable",
        "ai_reason",
        "processed",
        "uploaded",
        "final_image",
        "drive_file",
        "drive_link",
        "status"
    ]

    with open(
        REPORT_FILE,
        "a",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        if not file_exists:
            writer.writeheader()

        writer.writerow({
            "food_item": result.get("food_item", ""),
            "found_images": result.get("found", 0),
            "downloaded_images": result.get("downloaded", 0),
            "selected_image": result.get("selected_image", ""),
            "quality_score": result.get("quality_score", ""),
            "ai_food_match": result.get("ai_food_match", ""),
            "ai_confidence": result.get("ai_confidence", ""),
            "menu_suitable": result.get("menu_suitable", ""),
            "ai_reason": result.get("ai_reason", ""),
            "processed": result.get("processed", False),
            "uploaded": result.get("uploaded", False),
            "final_image": result.get("final_image", ""),
            "drive_file": result.get("drive_file", ""),
            "drive_link": result.get("drive_link", ""),
            "status": result.get("status", "")
        })

    print(f"Report updated: {REPORT_FILE}")


def load_processed_items():
    if not os.path.exists(CHECKPOINT_FILE):
        return set()

    with open(CHECKPOINT_FILE, "r", encoding="utf-8") as file:
        return {
            line.strip()
            for line in file
            if line.strip()
        }


def mark_item_processed(food_item):
    with open(
        CHECKPOINT_FILE,
        "a",
        encoding="utf-8"
    ) as file:
        file.write(food_item + "\n")



# ============================================================
# FIND ACTUAL DOWNLOADED IMAGE
# ============================================================

def find_actual_image_path(base_path):
    """
    The downloader can save JPG, PNG or WEBP.
    Find which file was actually created.
    """

    base_without_extension = os.path.splitext(base_path)[0]

    possible_files = [
        base_without_extension + ".jpg",
        base_without_extension + ".png",
        base_without_extension + ".webp"
    ]

    for file_path in possible_files:
        if os.path.exists(file_path):
            return file_path

    return None


# ============================================================
# FIND EXISTING DOWNLOADED IMAGES
# ============================================================

def get_existing_downloaded_images(food_download_folder):

    image_paths = []

    if not os.path.exists(food_download_folder):
        return image_paths

    allowed_extensions = (
        ".jpg",
        ".jpeg",
        ".png",
        ".webp"
    )

    for filename in os.listdir(food_download_folder):

        file_path = os.path.join(
            food_download_folder,
            filename
        )

        if not os.path.isfile(file_path):
            continue

        if filename.lower().endswith(
            allowed_extensions
        ):
            image_paths.append(file_path)

    return sorted(image_paths)


# ============================================================
# RESUME PROCESSING OF EXISTING DOWNLOADED IMAGES
# ============================================================

def resume_process_food_item(
    food_item,
    drive_service,
    drive_folder_id
):

    print("\n" + "=" * 70)
    print(f"RESUME PROCESSING: {food_item}")
    print("=" * 70)

    # --------------------------------------------------------
    # Download folder
    # --------------------------------------------------------

    safe_folder_name = create_safe_folder_name(
        food_item
    )

    food_download_folder = os.path.join(
        DOWNLOAD_FOLDER,
        safe_folder_name
    )

    # --------------------------------------------------------
    # Find existing downloaded images
    # --------------------------------------------------------

    existing_images = get_existing_downloaded_images(
        food_download_folder
    )

    print(
        f"Existing downloaded images: "
        f"{len(existing_images)}"
    )

    if not existing_images:

        print(
            "No downloaded images found. "
            "Skipping..."
        )

        return {
            "food_item": food_item,
            "downloaded": 0,
            "processed": False,
            "uploaded": False,
            "status": "No Existing Images"
        }

    # --------------------------------------------------------
    # Analyze image quality
    # --------------------------------------------------------

    print("\nAnalyzing existing images...")

    quality_results = []

    for image_path in existing_images:

        print(
            f"\nChecking: "
            f"{os.path.basename(image_path)}"
        )

        try:

            result = analyze_image(
                image_path
            )

        except Exception as error:

            print(
                f"Quality analysis error: "
                f"{error}"
            )

            continue

        if not result["valid"]:

            print(
                "Invalid image. Skipping."
            )

            continue

        print(
            f"Quality Score: "
            f"{result['quality_score']}"
        )

        print(
            f"Quality: "
            f"{result['quality']}"
        )

        quality_results.append(
            (
                image_path,
                result
            )
        )

    # --------------------------------------------------------
    # No valid images
    # --------------------------------------------------------

    if not quality_results:

        print(
            "\nNo valid images available "
            "for processing."
        )

        return {
            "food_item": food_item,
            "downloaded": len(existing_images),
            "processed": False,
            "uploaded": False,
            "status": "No Valid Images"
        }

    # --------------------------------------------------------
    # Select highest-quality image
    # --------------------------------------------------------

    best_image, best_quality = max(
        quality_results,
        key=lambda item: item[1]["quality_score"]
    )

    print("\n" + "-" * 60)

    print(
        f"Selected best image: "
        f"{os.path.basename(best_image)}"
    )

    print(
        f"Quality score: "
        f"{best_quality['quality_score']}"
    )

    print("-" * 60)

    # --------------------------------------------------------
    # Verify the selected image with Gemini before processing
    # --------------------------------------------------------

    print("\nChecking resumed image with AI...")

    try:
        ai_result = check_food_relevance(
            best_image,
            food_item
        )
    except Exception as error:
        print(f"AI verification error: {error}")
        return {
            "food_item": food_item,
            "downloaded": len(existing_images),
            "processed": False,
            "uploaded": False,
            "status": "AI Verification Failed"
        }

    if (
        not ai_result.get("food_match", False)
        or not ai_result.get("menu_suitable", False)
        or ai_result.get("confidence", 0) < MIN_AI_CONFIDENCE
    ):
        print(
            "Resumed image rejected by AI: "
            f"match={ai_result.get('food_match', False)}, "
            f"menu_suitable={ai_result.get('menu_suitable', False)}, "
            f"confidence={ai_result.get('confidence', 0)}"
        )
        return {
            "food_item": food_item,
            "downloaded": len(existing_images),
            "processed": False,
            "uploaded": False,
            "status": "AI Rejected Image"
        }

    # --------------------------------------------------------
    # Create processed folder
    # --------------------------------------------------------

    processed_folder = os.path.join(
        PROCESSED_FOLDER,
        safe_folder_name
    )

    os.makedirs(
        processed_folder,
        exist_ok=True
    )

    # --------------------------------------------------------
    # IMPORTANT:
    # Final filename = exact food item name
    # --------------------------------------------------------

    processed_output_path = os.path.join(
        processed_folder,
        f"{food_item}.jpg"
    )

    print(
        f"\nProcessing image..."
    )

    print(
        f"Output: "
        f"{processed_output_path}"
    )

    # --------------------------------------------------------
    # Process image
    # --------------------------------------------------------

    try:

        processing_result = process_image(
            best_image,
            processed_output_path
        )

    except Exception as error:

        print(
            f"Image processing error: "
            f"{error}"
        )

        return {
            "food_item": food_item,
            "downloaded": len(existing_images),
            "processed": False,
            "uploaded": False,
            "status": "Processing Error"
        }

    if not processing_result["success"]:

        print(
            "Image processing failed: "
            f"{processing_result.get('error')}"
        )

        return {
            "food_item": food_item,
            "downloaded": len(existing_images),
            "processed": False,
            "uploaded": False,
            "status": "Processing Failed"
        }

    print(
        "\nImage processing successful ✓"
    )

    # --------------------------------------------------------
    # Upload to Google Drive
    # --------------------------------------------------------

    uploaded = False

    try:

        uploaded_file = upload_file_to_drive(
            drive_service,
            processing_result["output_path"],
            drive_folder_id
        )

        uploaded = True

        print(
            f"\nUploaded to Google Drive ✓"
        )

        print(
            f"Drive file: "
            f"{uploaded_file['name']}"
        )

    except Exception as error:

        print(
            f"\nGoogle Drive upload error: "
            f"{error}"
        )


    report_result = {
        "food_item": food_item,
        "downloaded": len(existing_images),
        "selected_image": os.path.basename(best_image),
        "quality_score": best_quality["quality_score"],
        "processed": True,
        "uploaded": uploaded,
        "status": (
            "Success"
            if uploaded
            else "Processed - Upload Failed"
        )
    }

    save_processing_report(report_result)

    # --------------------------------------------------------
    # Final result
    # --------------------------------------------------------

    return {
        "food_item": food_item,
        "downloaded": len(existing_images),
        "processed": True,
        "uploaded": uploaded,
        "status": (
            "Success"
            if uploaded
            else "Processed - Upload Failed"
        )
    }


# ============================================================
# PROCESS ONE FOOD ITEM
# ============================================================

def process_food_item(food_item, drive_service, drive_folder_id):

    print("\n" + "=" * 70)
    print(f"Food Item: {food_item}")
    print("=" * 70)

    # --------------------------------------------------------
    # Create download folder
    # --------------------------------------------------------

    safe_folder_name = create_safe_folder_name(food_item)

    food_download_folder = os.path.join(
        DOWNLOAD_FOLDER,
        safe_folder_name
    )

    os.makedirs(
        food_download_folder,
        exist_ok=True
    )

    print(f"Download folder: {food_download_folder}")

    # --------------------------------------------------------
    # Existing image hashes
    # --------------------------------------------------------

    existing_hashes = get_existing_image_hashes(
        food_download_folder
    )

    # --------------------------------------------------------
    # Search images
    # --------------------------------------------------------

    print("\nSearching images...")

    try:

        results = search_images(
            food_item,
            num_results=NUM_RESULTS
        )

    except Exception as error:

        print(f"Image search failed: {error}")

        return {
            "food_item": food_item,
            "found": 0,
            "downloaded": 0,
            "processed": False,
            "status": "Search Failed"
        }

    # --------------------------------------------------------
    # No results
    # --------------------------------------------------------

    if not results:

        print("No image results found.")

        return {
            "food_item": food_item,
            "found": 0,
            "downloaded": 0,
            "processed": False,
            "status": "No Images Found"
        }

    print(f"Images found: {len(results)}")

    # --------------------------------------------------------
    # Tracking
    # --------------------------------------------------------

    downloaded_count = 0

    # Only images successfully downloaded during THIS run
    downloaded_image_paths = []
    quality_candidates = []

    # Only images approved by AI
    ai_approved_images = []
    ai_results = []

    # --------------------------------------------------------
    # Download + Validate + Quality + AI
    # --------------------------------------------------------

    for index, image in enumerate(results, start=1):

        print("\n" + "-" * 60)
        print(f"Candidate {index}")
        print("-" * 60)

        # ----------------------------------------------------
        # Image information
        # ----------------------------------------------------

        title = image.get(
            "title",
            "Unknown"
        )

        image_url = image.get(
            "image_url"
        )

        source = image.get(
            "source",
            "Unknown"
        )

        width = image.get(
            "width"
        )

        height = image.get(
            "height"
        )

        print(f"Title   : {title}")
        print(f"Source  : {source}")
        print(f"Size    : {width} x {height}")
        print(f"URL     : {image_url}")

        # ----------------------------------------------------
        # Check image URL
        # ----------------------------------------------------

        if not image_url:

            print("No image URL available. Skipping...")
            continue

        # ----------------------------------------------------
        # Candidate filename
        # ----------------------------------------------------

        file_name = f"candidate_{index:02d}.jpg"

        file_path = os.path.join(
            food_download_folder,
            file_name
        )

        print(f"Downloading -> {file_path}")

        # ----------------------------------------------------
        # Download + validation + retry + duplicate check
        # ----------------------------------------------------

        try:

            success = download_image(
                image_url,
                file_path,
                retries=3,
                existing_hashes=existing_hashes
            )

        except Exception as error:

            print(f"Download error: {error}")
            continue

        # ----------------------------------------------------
        # Download successful
        # ----------------------------------------------------

        if not success:

            print("Download failed ✗")
            continue

        downloaded_count += 1

        print("Download successful ✓")

        # ----------------------------------------------------
        # Find actual downloaded file
        # ----------------------------------------------------

        actual_file_path = find_actual_image_path(
            file_path
        )

        if not actual_file_path:

            print(
                "Downloaded image file "
                "could not be located."
            )

            continue

        print(
            f"Actual file: {actual_file_path}"
        )

        # ====================================================
        # IMAGE QUALITY CHECK
        # ====================================================

        print("\nAnalyzing image quality...")

        try:

            quality_result = analyze_image(
                actual_file_path
            )

        except Exception as error:

            print(
                f"Quality analysis error: {error}"
            )

            continue

        if not quality_result["valid"]:

            print(
                "Quality analysis failed: "
                f"{quality_result.get('reason', 'Unknown')}"
            )

            continue

        print(
            f"Quality Score : "
            f"{quality_result['quality_score']}"
        )

        print(
            f"Quality       : "
            f"{quality_result['quality']}"
        )

        print(
            f"Blur Score    : "
            f"{quality_result['blur_score']}"
        )

        print(
            f"Resolution    : "
            f"{quality_result['width']}x"
            f"{quality_result['height']}"
        )

        print(
            f"Aspect Score  : "
            f"{quality_result['aspect_ratio_score']}"
        )

        # ====================================================
        # STORE QUALITY CANDIDATE
        # ====================================================

        quality_candidates.append({
            "path": actual_file_path,
            "quality_score": quality_result["quality_score"]
        })

        print(
            f"Candidate stored for AI verification "
            f"(Quality Score: {quality_result['quality_score']})"
        )

    # ========================================================
    # SELECT TOP QUALITY CANDIDATES FOR AI
    # ========================================================

    quality_candidates.sort(
        key=lambda x: x["quality_score"],
        reverse=True
    )

    top_ai_candidates = quality_candidates[:2]

    print("\n" + "=" * 60)
    print("TOP CANDIDATES SELECTED FOR AI")
    print("=" * 60)

    for candidate in top_ai_candidates:
        print(
            f"{candidate['path']} "
            f"| Quality Score: {candidate['quality_score']}"
        )

    # ========================================================
    # AI FOOD RELEVANCE CHECK
    # ========================================================

    ai_approved_images = []

    for candidate in top_ai_candidates:

        actual_file_path = candidate["path"]

        print("\nChecking food relevance with AI...")
        print(f"Image: {actual_file_path}")

        try:
            ai_result = check_food_relevance(
                actual_file_path,
                food_item
            )

        except Exception as error:

            print(f"AI check failed: {error}")
            continue

        food_match = ai_result.get(
            "food_match",
            False
        )

        menu_suitable = ai_result.get(
            "menu_suitable",
            False
        )

        confidence = ai_result.get(
            "confidence",
            0
        )

        reason = ai_result.get(
            "reason",
            "No reason provided."
        )


        ai_results.append({
            "image": actual_file_path,
            "food_match": food_match,
            "confidence": confidence,
            "menu_suitable": menu_suitable,
            "reason": reason
        })

        print(
            f"Menu Suitable → {menu_suitable}"
        )

        print(
            f"AI Match → {food_match} "
            f"| Menu Suitable → {menu_suitable} "
            f"| Confidence: {confidence}"
        )

        print(
            f"AI Reason → {reason}"
        )

        if not food_match:

            print("AI rejected this image ✗")
            continue

        if not menu_suitable:

            print("Image rejected for menu suitability ✗")
            continue

        if confidence < MIN_AI_CONFIDENCE:

            print(
                f"AI confidence {confidence}% "
                f"is below required "
                f"{MIN_AI_CONFIDENCE}%."
            )

            continue

        print("AI accepted this image ✓")

        ai_approved_images.append(
            actual_file_path
        )

    # ========================================================
    # AFTER ALL CANDIDATES
    # ========================================================

    print("\n" + "=" * 60)
    print("CANDIDATE ANALYSIS COMPLETE")
    print("=" * 60)

    print(
        f"Images downloaded : {downloaded_count}"
    )

    print(
        f"AI-approved images: "
        f"{len(ai_approved_images)}"
    )

    # ========================================================
    # NO AI-APPROVED IMAGE
    # ========================================================

    if not ai_approved_images:

        print(
            "\nNo AI-approved image found."
        )

        result = {
            "food_item": food_item,
            "found": len(results),
            "downloaded": downloaded_count,
            "ai_approved": 0,
            "ai_food_match": "",
            "ai_confidence": "",
            "menu_suitable": "",
            "ai_reason": (
                ai_results[-1]["reason"]
                if ai_results
                else "No AI-approved image found."
            ),
            "processed": False,
            "uploaded": False,
            "final_image": "",
            "drive_file": "",
            "drive_link": "",
            "status": "No Relevant Image Found"
        }
        save_processing_report(result)
        return result

    # ========================================================
    # PROCESS BEST AI-APPROVED IMAGE ONLY
    # ========================================================

    processed_count = 0
    uploaded_count = 0
    uploaded_file = None

    print("\n" + "=" * 60)
    print("PROCESSING BEST AI-APPROVED IMAGE")
    print("=" * 60)

    processed_folder = os.path.join(
        PROCESSED_FOLDER,
        safe_folder_name
    )

    os.makedirs(
        processed_folder,
        exist_ok=True
    )

    approved_quality_map = {
        candidate["path"]: candidate["quality_score"]
        for candidate in quality_candidates
    }

    best_approved_image = max(
        ai_approved_images,
        key=lambda path: approved_quality_map.get(path, 0)
    )

    selected_quality_score = approved_quality_map.get(
        best_approved_image,
        0
    )

    # IMPORTANT: exact food item filename required by assignment
    processed_output_path = os.path.join(
        processed_folder,
        f"{food_item}.jpg"
    )

    print(f"\nSelected final image: {best_approved_image}")
    print(f"Final quality score: {selected_quality_score}")
    print(f"Final output: {processed_output_path}")

    try:
        processing_result = process_image(
            best_approved_image,
            processed_output_path
        )
    except Exception as error:
        print(f"Image processing error: {error}")
        processing_result = {"success": False, "error": str(error)}

    if not processing_result["success"]:
        print(
            "Image processing failed: "
            f"{processing_result.get('error', 'Unknown error')}"
        )
    else:
        processed_count = 1

        print(
            f"Processed image created: "
            f"{processing_result['output_path']}"
        )

        try:
            uploaded_file = upload_file_to_drive(
                drive_service,
                processing_result["output_path"],
                drive_folder_id
            )

            uploaded_count = 1

            print(
                f"Uploaded to Google Drive: "
                f"{uploaded_file['name']}"
            )

        except Exception as error:
            print(f"Google Drive upload error: {error}")

    # ========================================================
    # ITEM SUMMARY
    # ========================================================

    print("\n" + "-" * 60)

    print(
        f"Search results : {len(results)}"
    )

    print(
        f"Downloaded     : {downloaded_count}"
    )

    print(
        f"AI approved     : "
        f"{len(ai_approved_images)}"
    )

    print(
        f"Processed       : "
        f"{processed_count}"
    )

    print(
        f"Folder         : "
        f"{food_download_folder}"
    )

    print(
        f"Processed      : "
        f"{'Yes' if processed_count else 'No'}"
    )

    # --------------------------------------------------------
    # Determine status
    # --------------------------------------------------------

    if processed_count and uploaded_count == processed_count:

        status = "Success"

    elif processed_count:

        status = "Processed - Upload Failed"

    elif ai_approved_images:

        status = "AI Approved - Processing Failed"

    elif downloaded_count > 0:

        status = "Downloaded - No Relevant Image"

    else:

        status = "Download Failed"

    # --------------------------------------------------------
    # Get AI details for selected image
    # --------------------------------------------------------

    selected_ai_result = {}

    for ai_result in ai_results:

        if ai_result["image"] == best_approved_image:

            selected_ai_result = ai_result
            break


    # --------------------------------------------------------
    # Get Google Drive details
    # --------------------------------------------------------

    drive_file_name = ""
    drive_file_link = ""

    if uploaded_file:

        drive_file_name = uploaded_file.get(
            "name",
            ""
        )

        drive_file_link = uploaded_file.get(
            "webViewLink",
            ""
        )


    # --------------------------------------------------------
    # Final report result
    # --------------------------------------------------------

    final_result = {
        "food_item": food_item,
        "found": len(results),
        "downloaded": downloaded_count,

        "selected_image": (
            os.path.basename(best_approved_image)
            if ai_approved_images
            else ""
        ),

        "quality_score": (
            selected_quality_score
            if ai_approved_images
            else ""
        ),

        "ai_food_match": selected_ai_result.get(
            "food_match",
            ""
        ),

        "ai_confidence": selected_ai_result.get(
            "confidence",
            ""
        ),

        "menu_suitable": selected_ai_result.get(
            "menu_suitable",
            ""
        ),

        "ai_reason": selected_ai_result.get(
            "reason",
            ""
        ),

        "processed": bool(processed_count),

        "uploaded": (
            uploaded_count == processed_count
            and processed_count > 0
        ),

        "final_image": (
            os.path.basename(
                processing_result["output_path"]
            )
            if processed_count
            else ""
        ),

        "drive_file": drive_file_name,

        "drive_link": drive_file_link,

        "status": status
    }

    save_processing_report(final_result)

    return final_result


# ============================================================
# MAIN FUNCTION
# ============================================================

def main():

    print("\nConnecting to Google Drive...")
    drive_service = authenticate_google_drive()
    drive_folder_id = get_or_create_drive_folder(drive_service)
    print("Google Drive connected successfully.")

    print("\n")

    print("=" * 70)
    print(
        "        AI FOOD IMAGE AUTOMATION AGENT"
    )
    print("=" * 70)

    # ========================================================
    # PHASE 2
    # Read Excel
    # ========================================================

    print(
        "\n[PHASE 2] Reading Excel file..."
    )

    try:

        food_items = read_food_items(
            EXCEL_FILE
        )

    except Exception as error:

        print(
            f"\nExcel reading failed: {error}"
        )

        return

    print(
        f"\nTotal food items: "
        f"{len(food_items)}"
    )

    if not food_items:

        print(
            "No food items found in Excel."
        )

        return


        # ========================================================
    # RESUME MODE
    # Process already downloaded images
    # ========================================================

    if RESUME_MODE:

        print("\n")
        print("=" * 70)
        print("RESUME MODE ENABLED")
        print("=" * 70)

        resume_items = food_items[:TEST_ITEMS]

        print(
            f"Processing existing downloaded images "
            f"for {len(resume_items)} food items."
        )

        results_summary = []

        processed_items = load_processed_items()

        print(
            f"Already processed items: {len(processed_items)}"
        )

        for index, food_item in enumerate(
            resume_items,
            start=1
        ):

            if food_item in processed_items:
                print(
                    f"Skipping already processed: {food_item}"
                )
                continue

            print("\n")
            print(
                f"RESUME PROCESSING "
                f"{index}/{len(resume_items)}"
            )

            try:

                result = resume_process_food_item(
                    food_item,
                    drive_service,
                    drive_folder_id
                )

                results_summary.append(
                    result
                )

                if result.get("processed") and result.get("uploaded"):
                    mark_item_processed(food_item)
                    processed_items.add(food_item)

                    print(
                        f"Checkpoint saved: {food_item}"
                    )

            except Exception as error:

                print(
                    f"Unexpected error for "
                    f"{food_item}: {error}"
                )

                results_summary.append({
                    "food_item": food_item,
                    "downloaded": 0,
                    "processed": False,
                    "uploaded": False,
                    "status": "Error"
                })

        # ----------------------------------------------------
        # Resume summary
        # ----------------------------------------------------

        print("\n")
        print("=" * 70)
        print("RESUME PROCESSING COMPLETE")
        print("=" * 70)

        for result in results_summary:

            print(
                f"{result['food_item']} "
                f"→ Existing Images: "
                f"{result.get('downloaded', 0)} "
                f"| Processed: "
                f"{'Yes' if result.get('processed') else 'No'} "
                f"| Uploaded: "
                f"{'Yes' if result.get('uploaded') else 'No'} "
                f"| {result.get('status')}"
            )

        print("\nResume mode finished.")

        return

    # ========================================================
    # TEST MODE
    # ========================================================

    if TEST_MODE:

        print("\n")

        print("=" * 70)
        print("TEST MODE ENABLED")

        test_count = min(
            TEST_ITEMS,
            len(food_items)
        )

        print(
            f"Processing first "
            f"{test_count} food items."
        )

        print("=" * 70)

        test_items = food_items[
            :test_count
        ]

        results_summary = []

        # ----------------------------------------------------
        # Process test items
        # ----------------------------------------------------

        for index, food_item in enumerate(
            test_items,
            start=1
        ):

            print("\n")

            print(
                f"TEST PROCESSING "
                f"{index}/{len(test_items)}"
            )

            try:

                result = process_food_item(
                    food_item,
                    drive_service,
                    drive_folder_id
                )

                results_summary.append(
                    result
                )


            except Exception as error:

                print(
                    f"Unexpected error for "
                    f"{food_item}: {error}"
                )

                results_summary.append({

                    "food_item": food_item,
                    "found": 0,
                    "downloaded": 0,
                    "ai_approved": 0,
                    "processed": False,
                    "status": "Error"

                })

        # ----------------------------------------------------
        # Test summary
        # ----------------------------------------------------

        print("\n")

        print("=" * 70)
        print("TEST COMPLETE")
        print("=" * 70)

        print()

        for result in results_summary:

            print(
                f"{result['food_item']} "
                f"→ Found: {result['found']} "
                f"| Downloaded: "
                f"{result['downloaded']} "
                f"| AI Approved: "
                f"{result.get('ai_approved', 0)} "
                f"| Processed: "
                f"{'Yes' if result['processed'] else 'No'} "
                f"| {result['status']}"
            )

        print("\n")

        print(
            "Test mode finished."
        )

        print(
            "Set TEST_MODE = False "
            "only after testing is successful."
        )

        return

    # ========================================================
    # FULL AUTOMATION MODE
    # ========================================================

    print("\n")

    print("=" * 70)
    print("FULL AUTOMATION MODE")

    print(
        f"Processing "
        f"{len(food_items)} food items..."
    )

    print("=" * 70)

    results_summary = []

    processed_items = load_processed_items()

    print(
        f"Already processed items: {len(processed_items)}"
    )

    # --------------------------------------------------------
    # Process every food item
    # --------------------------------------------------------

    for index, food_item in enumerate(
        food_items,
        start=1
    ):

        if food_item in processed_items:
            print(
                f"Skipping already processed: {food_item}"
            )
            continue

        print("\n")

        print(
            f"PROCESSING "
            f"{index}/{len(food_items)}"
        )

        try:

            result = process_food_item(
                food_item,
                drive_service,
                drive_folder_id
            )

            results_summary.append(
                result
            )

            if result.get("processed") and result.get("uploaded"):
                mark_item_processed(food_item)
                processed_items.add(food_item)

                print(
                    f"Checkpoint saved: {food_item}"
                )

        except Exception as error:

            print(
                f"Unexpected error for "
                f"{food_item}: {error}"
            )

            results_summary.append({

                "food_item": food_item,
                "found": 0,
                "downloaded": 0,
                "ai_approved": 0,
                "processed": False,
                "status": "Error"

            })

            continue

    # ========================================================
    # FINAL SUMMARY
    # ========================================================

    print("\n")

    print("=" * 70)
    print("PROCESSING COMPLETE")
    print("=" * 70)

    total_items = len(
        results_summary
    )

    total_found = sum(
        result["found"]
        for result in results_summary
    )

    total_downloaded = sum(
        result["downloaded"]
        for result in results_summary
    )

    total_ai_approved = sum(
        result.get("ai_approved", 0)
        for result in results_summary
    )

    processed_items = sum(
        1
        for result in results_summary
        if result["processed"]
    )

    failed_items = (
        total_items -
        processed_items
    )

    print(
        f"Total food items       : "
        f"{total_items}"
    )

    print(
        f"Total images found     : "
        f"{total_found}"
    )

    print(
        f"Total images downloaded: "
        f"{total_downloaded}"
    )

    print(
        f"Total AI-approved      : "
        f"{total_ai_approved}"
    )

    print(
        f"Successfully processed : "
        f"{processed_items}"
    )

    print(
        f"Failed items           : "
        f"{failed_items}"
    )

    print(
        f"\nImages saved inside: "
        f"{DOWNLOAD_FOLDER}/"
    )

    print(
        f"Processed images inside: "
        f"{PROCESSED_FOLDER}/"
    )

    print(
        "\nAgent finished."
    )


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()