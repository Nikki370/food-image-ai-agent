from src.image_search import search_images


food_item = "Paneer Tikka Masala"

print(f"\nSearching images for: {food_item}")
print("-" * 60)


results = search_images(
    food_item,
    num_results=5
)


print(f"Images found: {len(results)}")
print()


for index, image in enumerate(results, start=1):

    print(f"IMAGE {index}")
    print(f"Title: {image['title']}")
    print(f"Image URL: {image['image_url']}")
    print(f"Source: {image['source']}")
    print(f"Source URL: {image['source_url']}")
    print(
        f"Size: "
        f"{image['width']} x {image['height']}"
    )

    print("-" * 60)