import os
import json
import base64
import time

from dotenv import load_dotenv
from google import genai

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


def check_food_relevance(image_path, food_name):

    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not found in .env file.")

    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    client = genai.Client(api_key=GEMINI_API_KEY)

    # Read image
    with open(image_path, "rb") as image_file:
        image_bytes = image_file.read()

    # Detect MIME type
    extension = os.path.splitext(image_path)[1].lower()

    mime_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp"
    }

    mime_type = mime_types.get(extension, "image/jpeg")

    # Convert image to Base64
    image_data = base64.b64encode(image_bytes).decode("utf-8")

    prompt = f"""
You are an AI quality-control system for a restaurant menu image collection project.

Requested food item:
"{food_name}"

Carefully analyze the provided image.

Check ALL of the following:

1. Does the image clearly show the requested food item?
2. Is the dish visually consistent with the requested food?
3. Is the food the main subject of the image?
4. Is the dish clearly visible and reasonably centered?
5. Is the image sufficiently clear and not significantly blurry?
6. Is the dish unnecessarily cropped?
7. Does the image contain prominent text, advertisements, logos, watermarks,
   social-media overlays, or other elements that make it unsuitable for a
   restaurant menu?
8. Overall, is this image suitable as a clean restaurant menu image?

IMPORTANT:
- If the image shows a different dish, food_match must be false.
- If the image is ambiguous, food_match must be false.
- If the image has prominent text, watermark, advertisement, or social-media
  overlay, menu_suitable should normally be false.
- A small normal restaurant logo is acceptable if it does not interfere with
  the food.
- The food should be the main visual subject.
- Do not approve an image merely because it contains a similar-looking dish.

Return ONLY valid JSON.

Use exactly this format:

{{
    "food_match": true,
    "menu_suitable": true,
    "confidence": 95,
    "reason": "Short explanation"
}}

Rules:

- food_match must be true or false.
- menu_suitable must be true or false.
- confidence must be an integer from 0 to 100.
- reason must briefly explain the decision.
- Do not include Markdown.
- Do not include ```json.
- Return JSON only.
"""

    # Gemini retry for temporary errors
    max_attempts = 3

    for attempt in range(max_attempts):

        try:

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    {
                        "text": prompt
                    },
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": image_data
                        }
                    }
                ]
            )

            raw_response = response.text.strip()

            # Remove accidental Markdown code fences
            if raw_response.startswith("```"):
                raw_response = raw_response.replace("```json", "")
                raw_response = raw_response.replace("```", "")
                raw_response = raw_response.strip()

            # Convert JSON text → Python dictionary
            try:
                result = json.loads(raw_response)

            except json.JSONDecodeError:

                return {
                    "food_match": False,
                    "menu_suitable": False,
                    "confidence": 0,
                    "reason": "AI returned invalid JSON."
                }

            # Validate fields
            food_match = result.get("food_match")
            menu_suitable = result.get("menu_suitable")
            confidence = result.get("confidence")
            reason = result.get("reason")

            if not isinstance(food_match, bool):
                food_match = False

            if not isinstance(menu_suitable, bool):
                menu_suitable = False

            if not isinstance(confidence, int):
                confidence = 0

            if not isinstance(reason, str):
                reason = "No reason provided."

            return {
                "food_match": food_match,
                "menu_suitable": menu_suitable,
                "confidence": confidence,
                "reason": reason
            }

        except Exception as error:

            error_text = str(error)

            print(
                f"Gemini request failed "
                f"(attempt {attempt + 1}/{max_attempts}): "
                f"{type(error).__name__}: {error_text}"
            )

            # Retry temporary Gemini availability/quota errors
            if (
                "503" in error_text
                or "UNAVAILABLE" in error_text
                or "429" in error_text
                or "RESOURCE_EXHAUSTED" in error_text
            ):

                if attempt < max_attempts - 1:

                    wait_time = 2 ** attempt

                    print(
                        f"Gemini temporary error. "
                        f"Retrying in {wait_time} seconds..."
                    )

                    time.sleep(wait_time)
                    continue

                return {
                    "food_match": False,
                    "menu_suitable": False,
                    "confidence": 0,
                    "reason": (
                        "Gemini temporarily unavailable after retries: "
                        f"{error_text}"
                    )
                }

            # Other unexpected errors
            return {
                "food_match": False,
                "menu_suitable": False,
                "confidence": 0,
                "reason": f"AI verification failed: {error_text}"
            }