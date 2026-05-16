import os
import zipfile
root = r'C:/Users/varun/Downloads/NLP_DOMAIN_BASED NEWS SUMMARIZATION'
zip_path = os.path.join(os.path.dirname(root), 'NLP_DOMAIN_BASED_NEWS_SUMMARIZATION_no_deps.zip')
exclude_dirs = {'node_modules', '.venv', '__pycache__', '.next'}
with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
    for dirpath, dirnames, filenames in os.walk(root):
        relative_dir = os.path.relpath(dirpath, root)
        parts = [] if relative_dir == '.' else relative_dir.split(os.sep)
        if any(part in exclude_dirs for part in parts):
            continue
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
        for fname in filenames:
            file_path = os.path.join(dirpath, fname)
            rel_path = os.path.relpath(file_path, root)
            zf.write(file_path, rel_path)
print('Created', zip_path)
