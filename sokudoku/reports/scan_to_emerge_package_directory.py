import os
import shutil
import argparse

class PackageGenerator:
    def __init__(self, cut_to_create):
        self.cut_to_create = cut_to_create
        self.package_content = {}

    def parse_package_content(self, package_file):
        with open(package_file, 'r') as f:
            current_dir = ''
            for line in f:
                line = line.strip()
                if line.startswith('package.'):
                    dir_name = line.split('.')[1]
                    self.package_content[dir_name] = []
                    current_dir = dir_name
                elif line:
                    self.package_content[current_dir].append(line)

    def generate_directories(self):
        for dir_name in self.package_content:
            dir_path = os.path.join('.', dir_name)
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)

    def generate_source_files(self):
        for dir_name, content in self.package_content.items():
            for i, line in enumerate(content):
                if line.startswith(self.cut_to_create):
                    file_name = f"{dir_name.replace('/', '_')}.c"
                    file_path = os.path.join('.', dir_name, file_name)
                    with open(file_path, 'w') as f:
                        f.write('\n'.join(content[i+1:]))
                    break

def main():
    parser = argparse.ArgumentParser(description='Package Generator')
    parser.add_argument('-cut_to_create', type=str, required=True, help='The line to cut the source code from')
    parser.add_argument('package_file', type=str, help='The file containing the package content')
    args = parser.parse_args()

    package_generator = PackageGenerator(args.cut_to_create)
    package_generator.parse_package_content(args.package_file)
    package_generator.generate_directories()
    package_generator.generate_source_files()

if __name__ == '__main__':
    main()
