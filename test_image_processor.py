from src.image_processor import process_image


input_image = (
    "downloads/Chicken Tandoori/candidate_05.jpg"
)

output_image = (
    "processed/Chicken Tandoori_test.jpg"
)


result = process_image(
    input_image,
    output_image
)


print("\n")
print("=" * 60)
print("IMAGE PROCESSING RESULT")
print("=" * 60)

for key, value in result.items():
    print(f"{key}: {value}")