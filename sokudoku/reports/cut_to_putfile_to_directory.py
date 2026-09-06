import os
import argparse

class PackageExtractor:
    def __init__(self, package_file):
        self.package_file = package_file
        self.package_content = {}

    def parse_package_content(self):
        with open(self.package_file, 'r') as f:
            current_dir = ''
            for line in f:
                line = line.strip()
                if line.startswith('package.'):
                    dir_name = line.split('.')[1]
                    self.package_content[dir_name] = []
                    current_dir = dir_name
                elif line:
                    self.package_content[current_dir].append(line)

    def extract_source_files(self):
        for dir_name, content in self.package_content.items():
            file_name = f"{dir_name.replace('/', '_')}.c"
            file_path = os.path.join('.', dir_name, file_name)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w') as f:
                f.write('\n'.join(content))

def main():
    parser = argparse.ArgumentParser(description='Package Extractor')
    parser.add_argument('--file', type=str, required=True, help='The package file to extract from')
    args = parser.parse_args()

    package_extractor = PackageExtractor(args.file)
    package_extractor.parse_package_content()
    package_extractor.extract_source_files()

if __name__ == '__main__':
    main()
