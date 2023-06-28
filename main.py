import os
import time
import shutil
import zipfile
import tarfile
import py7zr
import argparse
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


# Function to check if a file is a media file based on its extension
def is_media_file(filename):
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.heic', '.nef', '.tiff', 'webp', '.dng.'}
    video_extensions = {'.mp4', '.avi', '.mov', '.flv', '.mp', '.m4v', '.wmv'}
    ext = os.path.splitext(filename)[1]
    return ext in image_extensions or ext in video_extensions


# Function to rename files with .mp extension to .mp4
def rename_mp_to_mp4(filepath):
    if filepath.endswith('.mp'):
        base = os.path.splitext(filepath)[0]
        new_filepath = base + '.mp4'
        os.rename(filepath, new_filepath)
        return new_filepath
    return filepath


# Function to unarchive different types of compressed files
def unarchive(file_path):
    if file_path.endswith('.zip'):
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(file_path[:-4])
        os.remove(file_path)
    elif file_path.endswith('.tar'):
        with tarfile.TarFile(file_path, 'r') as tar_ref:
            tar_ref.extractall(file_path[:-4])
        os.remove(file_path)
    elif file_path.endswith('.tar.gz'):
        with tarfile.TarFile.gzopen(file_path, 'r') as tar_ref:
            tar_ref.extractall(file_path[:-7])
        os.remove(file_path)
    elif file_path.endswith('.7z'):
        with py7zr.SevenZipFile(file_path, mode='r') as z:
            z.extractall(file_path[:-3])
        os.remove(file_path)


# Function to move file from source to target directory without overwriting existing files
def move_file(src, dst, target_dir):
    base = os.path.basename(src)
    while os.path.exists(dst):
        name, ext = os.path.splitext(base)
        name += "_1"
        base = name + ext
        dst = os.path.join(target_dir, base)
    shutil.move(src, dst)


# Event handler for file system events
class Handler(FileSystemEventHandler):
    def __init__(self, target_dir):
        super().__init__()
        self.target_dir = target_dir

    # Function to be called when a new file or directory is created
    def on_created(self, event):
        if not event.is_directory:
            unarchive(event.src_path)
            if is_media_file(event.src_path):
                src = rename_mp_to_mp4(event.src_path)
                dst = os.path.join(self.target_dir, os.path.basename(src))
                move_file(src, dst, self.target_dir)
        else:
            shutil.rmtree(event.src_path)


# Main function to set up file system observer
def main(source_dirs, target_dir):
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    event_handler = Handler(target_dir)
    observer = Observer()
    for source_dir in source_dirs:
        observer.schedule(event_handler, path=source_dir, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()


# Entry point of the script
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Monitor directories and move media files.')
    parser.add_argument('--source_dirs', nargs='+', default=['F:\\1-20TB\czkawka-storage\\adult-images-nested', 'C:\\Users\\Nicklas\\Downloads'], help='List of source directories to monitor.')
    parser.add_argument('--target_dir', default='F:\\1-20TB\czkawka-storage\\adult-images-flat', help='Target directory to move files to.')
    args = parser.parse_args()

    # Call the main function with user provided arguments
    main(args.source_dirs, args.target_dir)

