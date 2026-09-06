import os
import re
import argparse

class SourceCodeExtractor:
    def __init__(self, source_file):
        self.source_file = source_file
        self.source_code = {}

    def extract_source_code(self):
        with open(self.source_file, 'r') as f:
            content = f.read()
            sections = re.split(r'\/\/ package\.([\w\/]+)', content)
            for i in range(1, len(sections), 2):
                dir_path = sections[i]
                source_code = sections[i+1].strip()
                self.source_code[dir_path] = source_code

    def create_directories_and_files(self):
        for dir_path, code in self.source_code.items():
            dir_name = os.path.basename(dir_path)
            dir_path = os.path.join('.', os.path.dirname(dir_path))
            os.makedirs(dir_path, exist_ok=True)
            file_path = os.path.join(dir_path, f"{dir_name}.c")
            with open(file_path, 'w') as f:
                f.write(code)

def main():
    parser = argparse.ArgumentParser(description='Source Code Extractor')
    parser.add_argument('--file', type=str, required=True, help='The source code file to extract from')
    args = parser.parse_args()

    extractor = SourceCodeExtractor(args.file)
    extractor.extract_source_code()
    extractor.create_directories_and_files()

if __name__ == '__main__':
    main()
