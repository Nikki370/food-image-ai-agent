import pandas as pd
from pathlib import Path


def read_food_items(file_path):
    """
    Read food items from the Excel file.
    """

    file_path = Path(file_path)

    # Check whether file exists
    if not file_path.exists():
        raise FileNotFoundError(
            f"Excel file not found: {file_path}"
        )

    # Read Excel
    df = pd.read_excel(file_path)

    # Check required column
    if "item_name" not in df.columns:
        raise ValueError(
            "Required column 'item_name' was not found in Excel file."
        )

    # Remove empty values
    food_items = (
        df["item_name"]
        .dropna()
        .astype(str)
        .str.strip()
    )

    # Remove empty strings
    food_items = food_items[food_items != ""]

    return food_items.tolist()