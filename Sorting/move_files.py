#!/usr/bin/env python3
"""
move_files.py - Move (cut & paste) files from multiple source folders into one destination folder.

Usage:
    python3 move_files.py -d <destination_folder> <source_folder1> [source_folder2] ...

Options:
    -d, --dest DIR     Destination folder (required). Created if it doesn't exist.
    -r, --recursive    Also move files from subfolders of each source.
    -n, --dry-run       Show what would be moved without actually moving anything.

Examples:
    python3 move_files.py -d ~/Desktop/AllPhotos ~/Desktop/Camera1 ~/Desktop/Camera2
    python3 move_files.py -r -n -d ~/Desktop/AllDocs ~/Desktop/Folder1 ~/Desktop/Folder2

Notes:
    - If a file with the same name already exists in the destination, it will NOT be
      overwritten. A counter is appended instead, e.g. "photo.jpg" -> "photo (1).jpg".
    - Only files are moved; empty source folders are left behind (not deleted).
"""

import argparse
import shutil
import sys
from pathlib import Path


def unique_target(dest_dir: Path, filename: str) -> Path:
    target = dest_dir / filename
    if not target.exists():
        return target

    stem, suffix = Path(filename).stem, Path(filename).suffix
    counter = 1
    while True:
        candidate = dest_dir / f"{stem} ({counter}){suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def iter_files(source: Path, recursive: bool):
    if recursive:
        yield from (p for p in source.rglob("*") if p.is_file())
    else:
        yield from (p for p in source.iterdir() if p.is_file())


def main():
    parser = argparse.ArgumentParser(description="Move files from multiple folders into one destination folder.")
    parser.add_argument("-d", "--dest", required=True, help="Destination folder")
    parser.add_argument("-r", "--recursive", action="store_true", help="Include files in subfolders of each source")
    parser.add_argument("-n", "--dry-run", action="store_true", help="Preview actions without moving files")
    parser.add_argument("sources", nargs="+", help="Source folders to move files from")
    args = parser.parse_args()

    dest_dir = Path(args.dest).expanduser()
    if not args.dry_run:
        dest_dir.mkdir(parents=True, exist_ok=True)
    dest_resolved = dest_dir.resolve() if dest_dir.exists() else dest_dir

    for src in args.sources:
        src_dir = Path(src).expanduser()
        if not src_dir.is_dir():
            print(f"Warning: '{src}' is not a folder, skipping.", file=sys.stderr)
            continue

        for file_path in iter_files(src_dir, args.recursive):
            if file_path.resolve().parent == dest_resolved:
                continue  # already in destination

            target = unique_target(dest_dir, file_path.name)

            if args.dry_run:
                print(f"[DRY RUN] Would move: {file_path} -> {target}")
            else:
                shutil.move(str(file_path), str(target))
                print(f"Moved: {file_path} -> {target}")

    print("Done.")


if __name__ == "__main__":
    main()
