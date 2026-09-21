# AI Agent for Automated Food Image Collection & Processing

An AI-powered automation system that reads food items from an Excel file, searches for suitable food images online, validates and evaluates the images, processes the selected image, and automatically uploads the final image to Google Drive.

The system also generates detailed processing reports, summary reports, and error reports for monitoring the complete workflow.

---

## 1. Project Objective

The objective of this project is to automate the collection and processing of food images for restaurant/menu applications.

Instead of manually searching, downloading, checking, resizing, renaming, and uploading images, the AI agent performs these tasks automatically.

### Automated Workflow

```text
Excel Food Items
       ↓
Image Search
       ↓
Image Download
       ↓
Image Validation
       ↓
Image Quality Analysis
       ↓
AI Food Relevance Verification
       ↓
AI Menu Suitability Verification
       ↓
Best Image Selection
       ↓
Image Processing
       ↓
Exact Food Item Filename
       ↓
Google Drive Upload
       ↓
Processing Reports
```

---

# 2. Features

## Excel Input

- Reads food item names from an Excel file.
- Supports processing multiple food items automatically.
- The current sample Excel file contains 501 food items.
- The project test workflow was validated using 10 food items.

## Automated Image Search

- Searches online images using Google Images through SerpApi.
- Searches multiple image candidates for each food item.
- The number of search results can be configured.

## Image Download and Validation

The system:

- Downloads images automatically.
- Validates downloaded files.
- Checks image format.
- Checks image dimensions.
- Rejects invalid/non-image responses.
- Handles failed downloads with retries.
- Detects duplicate images using image hashes.

## Image Quality Analysis

Each downloaded image is evaluated using:

- Resolution
- Blur/sharpness
- Aspect ratio

A quality score is generated for each valid image.

## AI Food Relevance Verification

Google Gemini is used to evaluate candidate images.

The AI checks:

- Whether the image matches the requested food item.
- Whether the food is clearly visible.
- Whether the food is the main subject.
- Whether the image is suitable for a restaurant menu.
- Whether there are distracting watermarks or unsuitable elements.
- Whether the image has inappropriate framing/cropping.

The AI returns:

- Food match
- Menu suitability
- Confidence score
- Reason for acceptance/rejection

## Automatic Image Processing

The selected image is processed to:

- 1800 × 1200 pixels
- JPEG format
- High image quality
- RGB color mode
- Suitable menu presentation

## Automatic Naming

The final image is renamed using the exact food item name.

Example:

```text
Veg Fried Rice.jpg
Chicken Biryani Boneless.jpg
Butter Roti.jpg
Dal Khichdi Tadka.jpg
```

## Google Drive Upload

Processed images are automatically uploaded to the configured Google Drive folder.

The system also includes duplicate upload protection so that an already uploaded file is not uploaded again.

## Reporting

The system generates three reports:

```text
reports/
├── processing_report.csv
├── summary_report.csv
└── error_report.csv
```

### processing_report.csv

Contains detailed information for every food item, including:

- Food item
- Images found
- Images downloaded
- Selected image
- Quality score
- AI food match
- AI confidence
- Menu suitability
- AI reason
- Processing status
- Upload status
- Final image
- Google Drive file
- Google Drive link

### summary_report.csv

Contains overall project statistics such as:

- Total food items
- Total images found
- Total images downloaded
- AI-approved images
- Successfully processed images
- Successfully uploaded images
- Failed items
- Processing success rate
- Upload success rate

### error_report.csv

Contains failed items and their available failure information, including:

- Food item
- Status
- AI food match
- AI confidence
- Menu suitability
- AI reason

---

# 3. Technologies Used

## Programming Language

- Python

## AI

- Google Gemini API

## Image Processing

- Pillow (PIL)

## Data Processing

- Pandas
- OpenPyXL

## Image Search

- SerpApi Google Images API

## Cloud Storage

- Google Drive API

## Authentication

- Google OAuth 2.0

## Other Libraries

- Requests
- python-dotenv

---

# 4. Project Structure

```text
food-image-ai-agent/
│
├── config/
│
├── data/
│   └── food_items.xlsx
│
├── downloads/
│   └── <food-item-folders>/
│
├── processed/
│   └── <food-item-folders>/
│
├── reports/
│   ├── processing_report.csv
│   ├── summary_report.csv
│   └── error_report.csv
│
├── src/
│   ├── excel_reader.py
│   ├── food_ai.py
│   ├── google_drive.py
│   ├── image_downloader.py
│   ├── image_processor.py
│   ├── image_quality.py
│   └── image_search.py
│
├── main.py
├── generate_reports.py
├── requirements.txt
├── .env
├── credentials.json
├── token.json
├── drive_folder_id.txt
└── README.md
```

---

# 5. Input Excel File

The input Excel file is located at:

```text
data/food_items.xlsx
```

The Excel file contains food item information.

Important column:

```text
item_name
```

Example:

| menu_category | menu_sub_category | item_name |
|---|---|---|
| Main Course | Tandoori | Chicken Tandoori |
| Rice | Fried Rice | Veg Fried Rice |
| Main Course | Biryani | Chicken Biryani Boneless |
| Bread | Indian Bread | Butter Roti |

---

# 6. Configuration

The main configuration is available in:

```text
main.py
```

Important settings:

```python
EXCEL_FILE = "data/food_items.xlsx"

DOWNLOAD_FOLDER = "downloads"

PROCESSED_FOLDER = "processed"

REPORT_FOLDER = "reports"

NUM_RESULTS = 3

TEST_MODE = True

TEST_ITEMS = 10

MIN_AI_CONFIDENCE = 70

RESUME_MODE = False
```

## NUM_RESULTS

Controls the number of image search results considered for each food item.

Example:

```python
NUM_RESULTS = 3
```

## TEST_MODE

When enabled, only a limited number of food items are processed.

```python
TEST_MODE = True
```

## TEST_ITEMS

Controls the number of items processed during testing.

```python
TEST_ITEMS = 10
```

## MIN_AI_CONFIDENCE

Minimum Gemini confidence required for an image to be accepted.

```python
MIN_AI_CONFIDENCE = 70
```

---

# 7. Environment Variables

Create a `.env` file in the project root.

Example:

```env
SERPAPI_API_KEY=your_serpapi_api_key
GEMINI_API_KEY=your_gemini_api_key
```

Do not commit API keys to GitHub.

---

# 8. Google Drive Setup

The application uses Google Drive API for automatic image uploads.

Required file:

```text
credentials.json
```

This file contains the OAuth client credentials created in Google Cloud.

On the first authentication, the application creates:

```text
token.json
```

The application also stores the destination Google Drive folder ID in:

```text
drive_folder_id.txt
```

The Drive folder used by the application is:

```text
Food Image AI Agent
```

---

# 9. Installation

Clone or download the project.

Open a terminal inside the project directory.

Create a virtual environment:

```bash
python -m venv venv
```

Activate the virtual environment.

## Windows

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

# 10. Running the Automation

Run:

```bash
python main.py
```

When test mode is enabled:

```python
TEST_MODE = True
TEST_ITEMS = 10
```

the system processes the configured test items.

---

# 11. Generating Reports

After the processing report has been generated, run:

```bash
python generate_reports.py
```

This generates:

```text
reports/summary_report.csv
reports/error_report.csv
```

The detailed report remains:

```text
reports/processing_report.csv
```

---

# 12. Output

Downloaded candidate images are stored inside:

```text
downloads/
```

Example:

```text
downloads/
└── Veg Fried Rice/
    ├── candidate_01.jpg
    ├── candidate_02.jpg
    └── candidate_03.jpg
```

Processed images are stored inside:

```text
processed/
```

Example:

```text
processed/
└── Veg Fried Rice/
    └── Veg Fried Rice.jpg
```

---

# 13. Google Drive Output

The final processed image is automatically uploaded to the configured Google Drive folder.

Example:

```text
Veg Fried Rice.jpg
Chicken Biryani Boneless.jpg
Butter Roti.jpg
Dal Khichdi Tadka.jpg
```

The Google Drive file name and share/view link are stored in:

```text
processing_report.csv
```

---

# 14. AI Image Selection Logic

For each food item, the system follows this process:

```text
Search Images
      ↓
Download Candidates
      ↓
Validate Images
      ↓
Calculate Quality Score
      ↓
Select Top Quality Candidates
      ↓
Gemini AI Verification
      ↓
Check Food Match
      ↓
Check Menu Suitability
      ↓
Check Confidence
      ↓
Select Best Approved Image
```

An image is accepted only when:

```text
Food Match = True
AND
Menu Suitable = True
AND
Confidence >= Minimum Required Confidence
```

---

# 15. Image Processing Requirements

The final image is processed to:

```text
Width  = 1800 pixels
Height = 1200 pixels
Format = JPEG
```

The image is resized and cropped while maintaining the required output dimensions.

The system also checks the final output size to ensure it remains within the assignment requirement.

---

# 16. Error Handling

The system handles several types of failures.

## Image Search Failure

If image search fails, the food item is recorded with an appropriate status.

## Download Failure

Failed image downloads are retried automatically.

## Invalid Image

Non-image responses and invalid image files are rejected.

## Duplicate Image

Duplicate downloaded images are detected using image hashes.

## AI Rejection

Images that do not match the food item or are unsuitable for a menu are rejected.

## AI/API Temporary Errors

Temporary Gemini API errors are retried before the image is rejected.

## Google Drive Upload Failure

If image processing succeeds but Google Drive upload fails, the item is recorded with an upload failure status.

---

# 17. Checkpoint / Resume Support

The system maintains a checkpoint file:

```text
processed_items.txt
```

Successfully processed and uploaded food items can be recorded in this file.

This allows the full automation workflow to skip already completed items when resume/full processing is used.

---

# 18. Sample Test Result

The automation was tested using 10 food items.

Successful examples included:

```text
Veg Fried Rice
Chicken Biryani Boneless
Butter Roti
Dal Khichdi Tadka
```

For successful items, the complete workflow was completed:

```text
Image Search
    ↓
Image Download
    ↓
Quality Analysis
    ↓
Gemini Verification
    ↓
Image Processing
    ↓
Google Drive Upload
```

Some images were intentionally rejected because of reasons such as:

- Prominent watermarks
- Incorrect food item
- Food not being the main subject
- Unsuitable menu presentation

These rejections are recorded in the processing and error reports.

---

# 19. Security

The following files contain sensitive credentials or authentication information and should not be committed to Git:

```text
.env
credentials.json
token.json
```

The project should use `.gitignore` to prevent accidental upload of these files.

Example:

```gitignore
.env
venv/
__pycache__/
*.pyc
credentials.json
token.json
drive_folder_id.txt
```

---

# 20. Project Deliverables

The project provides:

- Automated food image search
- Automated image downloading
- Image validation
- Image quality analysis
- AI-based food relevance verification
- AI-based menu suitability verification
- Automatic image processing
- Automatic image renaming
- Google Drive upload
- Duplicate upload protection
- Detailed processing report
- Summary report
- Error report
- Checkpoint support
- Source code
- Run instructions

---

# 21. Quick Start

```bash
# Activate environment
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run automation
python main.py

# Generate summary and error reports
python generate_reports.py
```

---

# 22. Final Workflow

```text
                 FOOD IMAGE AI AGENT
                         │
                         ▼
                  Excel Input File
                         │
                         ▼
                     Food Item
                         │
                         ▼
                  Google Image Search
                         │
                         ▼
                  Download Candidates
                         │
                         ▼
                   Image Validation
                         │
                         ▼
                   Quality Evaluation
                         │
                         ▼
                 Gemini AI Verification
                         │
               ┌─────────┴─────────┐
               │                   │
            Accepted            Rejected
               │                   │
               ▼                   ▼
        Best Image Selected     Error Report
               │
               ▼
        1800 × 1200 Processing
               │
               ▼
        Exact Food Item Name
               │
               ▼
         Google Drive Upload
               │
               ▼
        Processing Report
               │
          ┌────┴────┐
          ▼         ▼
       Summary    Errors
        Report    Report
```

---

## Author

**Nikita Kumari**

B.Sc. (Hons) Computer Science & Data Analytics  
IIT Patna

---

## Project Status

**Status: Working Prototype **

The complete automation workflow has been implemented and validated using a 10-item test dataset.