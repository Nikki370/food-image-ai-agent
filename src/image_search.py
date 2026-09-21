import os
import serpapi

from dotenv import load_dotenv


load_dotenv()

SERPAPI_KEY = os.getenv(
    "SERPAPI_KEY"
)


def build_search_query(food_name):

    return (
        f"{food_name} "
        f"Indian food dish restaurant"
    )


def search_images(
    food_name,
    num_results=5
):

    if not SERPAPI_KEY:

        raise ValueError(
            "SERPAPI_KEY not found "
            "in .env file."
        )

    query = build_search_query(
        food_name
    )

    client = serpapi.Client(
        api_key=SERPAPI_KEY
    )

    results = client.search(
        {
            "engine": "google_images",
            "q": query,
            "hl": "en",
            "gl": "in"
        }
    )

    image_results = results.get(
        "images_results",
        []
    )

    candidates = []

    for image in image_results[
        :num_results
    ]:

        candidates.append(
            {
                "food_item": food_name,

                "title": image.get(
                    "title"
                ),

                "image_url": image.get(
                    "original"
                ),

                "thumbnail_url": image.get(
                    "thumbnail"
                ),

                "source": image.get(
                    "source"
                ),

                "source_url": image.get(
                    "link"
                ),

                "width": image.get(
                    "original_width"
                ),

                "height": image.get(
                    "original_height"
                )
            }
        )

    return candidates