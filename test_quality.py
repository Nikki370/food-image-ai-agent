from src.image_quality import analyze_image


image_path = "downloads/Chicken Tandoori/candidate_01.jpg"

result = analyze_image(image_path)

print("\nIMAGE QUALITY RESULT")
print("=" * 50)

for key, value in result.items():
    print(f"{key}: {value}")