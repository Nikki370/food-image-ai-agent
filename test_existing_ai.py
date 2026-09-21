from src.food_ai import check_food_relevance
from src.excel_reader import read_food_items
import os

food_items = read_food_items("data/food_items.xlsx")

for food_item in food_items[:3]:

    folder = os.path.join(
        "downloads",
        food_item
    )

    if not os.path.exists(folder):
        print(f"No folder: {food_item}")
        continue

    images = [
        os.path.join(folder, f)
        for f in os.listdir(folder)
        if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
    ]

    if not images:
        print(f"No images: {food_item}")
        continue

    image = images[0]

    print("\n" + "=" * 60)
    print(food_item)
    print("Image:", image)
    print("=" * 60)

    result = check_food_relevance(
        image,
        food_item
    )

    print(result)