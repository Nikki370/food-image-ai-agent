from pathlib import Path

from src.food_ai import check_food_relevance


image_folder = Path("downloads") / "Chicken Tandoori"
image_files = sorted(
    path
    for path in image_folder.iterdir()
    if path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
)

if not image_files:
    raise FileNotFoundError(
        f"No test images found in: {image_folder}"
    )

image_path = str(image_files[0])

food_name = "Chicken Tandoori"


result = check_food_relevance(
    image_path,
    food_name
)


print("\n")
print("=" * 60)
print("AI FOOD RELEVANCE RESULT")
print("=" * 60)

print(result)