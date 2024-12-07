import os

# Path to the folder you want to extract the structure from
root_path = r"C:\Users\Adithya Nugraputra R\Documents\mahfudmd-ai"

# Output file to save the directory structure
output_file = r"C:\Users\Adithya Nugraputra R\Documents\mahfudmd-ai\directory_structure.txt"

def extract_directory_structure(root, output):
    with open(output, 'w', encoding='utf-8') as f:
        for dirpath, dirnames, filenames in os.walk(root):
            # Create a relative indentation for subdirectories
            level = dirpath.replace(root, '').count(os.sep)
            indent = ' ' * 4 * level
            f.write(f"{indent}{os.path.basename(dirpath)}/\n")
            subindent = ' ' * 4 * (level + 1)
            for filename in filenames:
                f.write(f"{subindent}{filename}\n")

def main():
    extract_directory_structure(root_path, output_file)
    print(f"Directory structure extracted to {output_file}")

if __name__ == "__main__":
    main()
