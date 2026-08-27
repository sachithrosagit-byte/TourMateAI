import os

dataset_dir = os.path.join("data", "dataset")

def fix_extensions():
    for root, _, files in os.walk(dataset_dir):
        for file in files:
            file_path = os.path.join(root, file)
            # If the file doesn't have an extension, add .jpg
            if not os.path.splitext(file)[1]:
                new_path = file_path + ".jpg"
                try:
                    os.rename(file_path, new_path)
                except Exception:
                    pass
            # Or if it has an extension that TF doesn't recognize
            elif file.lower().endswith(".webp"):
                 # Note: TF might not support webp via image_dataset_from_directory depending on version
                 pass

if __name__ == "__main__":
    fix_extensions()
    print("Finished fixing extensions.")
