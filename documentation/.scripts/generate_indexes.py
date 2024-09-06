import os
import urllib


def extract_first_header(file_path):
    """Extract the first header from a markdown file."""
    with open(file_path, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if line.startswith("#"):
                return line.replace('#', '')
    return None


def generate_readme(directory : str, folder_order : str = [], output_file : str ="README.md"):
    with open(directory+'/'+output_file, "w", encoding="utf-8") as readme:
        readme.write("# README Index\n\n")
        readme.write("This README file contains an index of all files in the documentation directory.\n\n")
        readme.write("## File List\n\n")

        note_file : str = directory+'/note.md'
        if os.path.exists(note_file):
            readme.write("\n## Additional Notes\n\n")
            with open(note_file, "r", encoding="utf-8") as note:
                readme.write(note.read())

        
        previous_folder = ""

        folder_lines : dict[str, list[str]] = {}

        for root, dirs, files in os.walk(directory):
            relative_folder = os.path.relpath(root, directory).replace("\\", "/") #use linux path structure

            #exclude . folders
            if relative_folder[0] == '.':
                continue

            if relative_folder != previous_folder:
                # Create a bold header for each new folder
                folder_lines[relative_folder] = []
                folder_lines[relative_folder].append(f"**{relative_folder}**\n\n")
                
                previous_folder = relative_folder

                #generate index in folder
                generate_readme(directory+"/"+relative_folder)

            for file in files:
                file_path = os.path.relpath(os.path.join(root, file), directory).replace("\\", "/") #use linux path structure
                file_path = urllib.parse.quote(file_path)
                
                if file == "README.md": #skip
                    continue

                if file.endswith(".md"):
                    first_header = extract_first_header(os.path.join(root, file))
                    if first_header:
                        folder_lines[relative_folder].append(f"- [{file}]({file_path}) - {first_header}")
                    else:
                        folder_lines[relative_folder].append(f"- [{file}]({file_path})")
                else:
                    folder_lines[relative_folder].append(f"- [{file}]({file_path})")

            # Add an extra line break between different folders
            if files:
                folder_lines[relative_folder].append("")

        #write output
        for folder in folder_lines:
            if folder in folder_order: #skip ordered folders for the end
                continue

            for line in folder_lines[folder]:
                readme.write(line + "\n")

        #write ordered output
        for folder in folder_order:
            if folder not in folder_lines: #not found
                continue

            for line in folder_lines[folder]:
                readme.write(line + "\n")



if __name__ == "__main__":
    # Change the working directory to the location of the script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    # Specify the directory you want to index
    directory_to_index = "../"
    generate_readme(directory_to_index, ["3rdparty", "3rdparty/protocols"])