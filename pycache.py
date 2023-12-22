import os

def create_init_files(directory):
    for root, dirs, _ in os.walk(directory):
        for d in dirs:
            init_file = os.path.join(root, d, '__init__.py')
            open(init_file, 'a').close()  # 'a' mode ensures that the file will be created if it doesn't exist.

# Set the directory to the 'src' folder of your package
src_directory = os.path.join(os.getcwd(), 'src')
create_init_files(src_directory)

print(f'__init__.py files created in all subdirectories of {src_directory}')