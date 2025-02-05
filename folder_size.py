import os

def get_folder_size(folder_path):
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(folder_path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(filepath)
                except (OSError, PermissionError) as e:
                    print(f"Warning: Could not access file '{filepath}' - {e}")
                    continue
    except (OSError, PermissionError) as e:
        print(f"Error: Unable to access folder '{folder_path}' - {e}")
    return total_size

def format_size(size_in_bytes):
    # Convert to MB or GB based on size
    size_in_mb = size_in_bytes / (1024 * 1024)
    if size_in_mb < 1024:
        return f"{size_in_mb:.2f} MB"
    else:
        size_in_gb = size_in_mb / 1024
        return f"{size_in_gb:.2f} GB"

def list_folder_contents(folder_path, sort_by="name"):
    folder_contents = []
    
    try:
        # List only immediate files and subfolders (not recursive)
        for name in os.listdir(folder_path):
            full_path = os.path.join(folder_path, name)
            if os.path.isdir(full_path):  # If it's a folder
                folder_size = get_folder_size(full_path)  # Get the size of the folder
                folder_contents.append({
                    "name": name,
                    "path": full_path,
                    "size": folder_size
                })
            elif os.path.isfile(full_path):  # If it's a file
                file_size = os.path.getsize(full_path)
                folder_contents.append({
                    "name": name,
                    "path": full_path,
                    "size": file_size
                })
    except (OSError, PermissionError) as e:
        print(f"Error: Unable to access folder '{folder_path}' - {e}")
        return []

    # Sort based on user input
    if sort_by == "size":
        folder_contents.sort(key=lambda x: x["size"], reverse=True)
    else:
        folder_contents.sort(key=lambda x: x["name"].lower())

    return folder_contents

def main():
    folder_path = input("Enter the folder path: ").strip()
    
    # Remove surrounding quotes if present (handle both single and double quotes)
    folder_path = folder_path.strip('"').strip("'")
    
    # Normalize the path (supports both '/' and '\\' in the path)
    folder_path = os.path.abspath(folder_path)
    
    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        folder_name = os.path.basename(folder_path)
        
        print(f"\nFolder: {folder_name}")
        
        # Ask if the user wants to see sorted contents
        sort_choice = int(input("Do you want to see the folder contents sorted by '1. size' or '2. name'? enter option by number: "))

        if sort_choice not in [1, 2]:
            print("Invalid choice, showing by name.")
            sort_choice = "name"
        
        if sort_choice == 1:
            sort_choice = 'name'
        elif sort_choice == 2:
            sort_choice = 'size'
        else:
            print("something went wrong")
        contents = list_folder_contents(folder_path, sort_choice)
        
        if contents:
            print("\nContents:")
            for item in contents:
                print(f"{item['name']} - {format_size(item['size'])}")
        else:
            print("No contents found or unable to access some files.")
    else:
        print("The provided path does not exist or is not a valid folder.")

if __name__ == "__main__":
    main()
