from src.google_drive import authenticate_google_drive


print("=" * 60)
print("GOOGLE DRIVE AUTHENTICATION TEST")
print("=" * 60)

try:

    service = authenticate_google_drive()

    # Test the connection by listing a few Drive files
    results = service.files().list(
        pageSize=5,
        fields="files(id, name)"
    ).execute()

    files = results.get(
        "files",
        []
    )

    print("\nGoogle Drive connection successful ✓")

    if files:

        print("\nFiles found:")

        for file in files:

            print(
                f"- {file['name']} "
                f"({file['id']})"
            )

    else:

        print(
            "\nNo files found in Drive."
        )

except Exception as error:

    print(
        f"\nGoogle Drive authentication failed:"
        f"\n{error}"
    )