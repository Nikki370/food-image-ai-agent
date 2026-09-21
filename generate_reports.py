import csv
import os

REPORT_FILE = "reports/processing_report.csv"
SUMMARY_FILE = "reports/summary_report.csv"
ERROR_FILE = "reports/error_report.csv"


def read_processing_report():
    with open(REPORT_FILE, "r", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def generate_summary_report(rows):

    total_items = len(rows)

    total_found = sum(
        int(row.get("found_images", 0) or 0)
        for row in rows
    )

    total_downloaded = sum(
        int(row.get("downloaded_images", 0) or 0)
        for row in rows
    )

    ai_approved = sum(
        1
        for row in rows
        if row.get("ai_food_match") == "True"
        and row.get("menu_suitable") == "True"
    )

    processed = sum(
        1
        for row in rows
        if row.get("processed") == "True"
    )

    uploaded = sum(
        1
        for row in rows
        if row.get("uploaded") == "True"
    )

    failed = total_items - processed

    processing_rate = (
        round((processed / total_items) * 100, 2)
        if total_items else 0
    )

    upload_rate = (
        round((uploaded / total_items) * 100, 2)
        if total_items else 0
    )

    summary = [
        ["Metric", "Value"],
        ["Total Food Items", total_items],
        ["Total Images Found", total_found],
        ["Total Images Downloaded", total_downloaded],
        ["AI Approved Images", ai_approved],
        ["Successfully Processed", processed],
        ["Successfully Uploaded", uploaded],
        ["Failed Items", failed],
        ["Processing Success Rate (%)", processing_rate],
        ["Upload Success Rate (%)", upload_rate],
    ]

    with open(
        SUMMARY_FILE,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)
        writer.writerows(summary)

    print(f"Summary report created: {SUMMARY_FILE}")


def generate_error_report(rows):

    error_rows = []

    for row in rows:

        if row.get("status") != "Success":

            error_rows.append([
                row.get("food_item", ""),
                row.get("status", ""),
                row.get("ai_food_match", ""),
                row.get("ai_confidence", ""),
                row.get("menu_suitable", ""),
                row.get("ai_reason", ""),
            ])

    with open(
        ERROR_FILE,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            "food_item",
            "status",
            "ai_food_match",
            "ai_confidence",
            "menu_suitable",
            "ai_reason"
        ])

        writer.writerows(error_rows)

    print(f"Error report created: {ERROR_FILE}")


def main():

    if not os.path.exists(REPORT_FILE):
        print("Processing report not found.")
        return

    rows = read_processing_report()

    if not rows:
        print("Processing report is empty.")
        return

    generate_summary_report(rows)
    generate_error_report(rows)

    print("\nReports generated successfully.")
    print(f"Total rows processed: {len(rows)}")


if __name__ == "__main__":
    main()