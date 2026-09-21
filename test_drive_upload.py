from src.google_drive import (
    authenticate_google_drive,
    create_drive_folder,
    upload_file_to_drive
)


print("=" * 60)
print("GOOGLE DRIVE UPLOAD TEST")
print("=" * 60)


try:

    # --------------------------------------------------------
    # Authenticate
    # --------------------------------------------------------

    service = authenticate_google_drive()

    # --------------------------------------------------------
    # Create test folder
    # --------------------------------------------------------

    folder_id = create_drive_folder(
        service,
        "Food Image AI Agent Test"
    )

    # --------------------------------------------------------
    # Test image
    # --------------------------------------------------------

    image_path = (
        "processed/"
        "Chicken Tandoori/"
        "Chicken Tandoori.jpg"
    )

    # --------------------------------------------------------
    # Upload
    # --------------------------------------------------------

    uploaded_file = upload_file_to_drive(
        service,
        image_path,
        folder_id
    )

    print("\n" + "=" * 60)
    print("UPLOAD TEST SUCCESSFUL ✓")
    print("=" * 60)

except Exception as error:

    print("\n" + "=" * 60)
    print("UPLOAD TEST FAILED ✗")
    print("=" * 60)

    print(error)