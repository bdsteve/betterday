import os

# Define the files to be concatenated
files_to_concatenate = [
    'config.py',
    'app/__init__.py',
    'app/routes.py',
    'app/models.py',
    'app/extensions.py',
    'app/forms.py',
    'app/utils.py',
    'app/templates/home.html',
    'app/templates/login.html',
    'app/templates/register.html',
    'app/templates/macros.html',
    'app/templates/doactivity.html',
    'app/templates/landing.html',
    'app/templates/schedules.html',
    'run.py'
]

# Define the output file
output_file = 'combined.txt'

def create_directory_tree(startpath):
    """Generate a string representation of the directory tree."""
    tree = []
    for root, dirs, files in os.walk(startpath, topdown=True):
        level = root.replace(startpath, '').count(os.sep)
        indent = ' ' * 4 * level
        tree.append(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            tree.append(f"{subindent}{f}")
    return '\n'.join(tree)

def concatenate_files(file_list, output_file):
    tree = create_directory_tree('.')  # Adjust '.' to the root of your project if necessary
    with open(output_file, 'w') as outfile:
        outfile.write("# Project Directory Structure\n")
        outfile.write(tree + "\n\n# End of Directory Structure\n\n")
        for file_name in file_list:
            if os.path.exists(file_name):
                with open(file_name, 'r') as infile:
                    outfile.write(f'# Start of {file_name}\n')
                    outfile.write(infile.read())
                    outfile.write(f'\n# End of {file_name}\n\n')
            else:
                print(f"File {file_name} does not exist.")

if __name__ == '__main__':
    concatenate_files(files_to_concatenate, output_file)
    print(f"Files concatenated into {output_file}")
