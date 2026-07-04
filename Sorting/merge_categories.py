#!/usr/bin/env python3
"""
merge_categories.py - Merge Google Drive/Takeout "split export" folders back into
one folder per category.

Background:
    Google Drive/Takeout sometimes splits a large folder export into numbered parts,
    named like:
        <Category Name>-20260701T104121Z-3-001
        <Category Name>-20260701T104121Z-3-002
        <Category Name>-20260701T104121Z-3-003
        ...
    Each of these part-folders contains exactly ONE nested subfolder named after the
    category, holding a portion of the actual files, e.g.:
        DISHWASH + HF-20260701T104121Z-3-001/DISHWASH + HF/<files>
        DISHWASH + HF-20260701T104121Z-3-002/DISHWASH + HF/<files>

This script scans a root folder (e.g. "Drive-Data"), groups all part-folders by their
category name, and moves every file from each part's nested subfolder into a single
consolidated folder named after the category, directly under the root
(e.g. "Drive-Data/DISHWASH + HF/").

If a plain category folder already exists (already-merged, e.g. "CLEANING LOGISTICS
HANDCRFT"), files are merged into it too.

Usage:
    python3 merge_categories.py -n <root_folder>          # dry run (preview only)
    python3 merge_categories.py <root_folder>              # actually merge
    python3 merge_categories.py -c "DISHWASH + HF" <root>  # only merge one category
    python3 merge_categories.py --delete-empty <root>      # also remove emptied part-folders

Notes:
    - Filename collisions are never overwritten; a counter is appended, e.g.
      "a123.mp4" -> "a123 (1).mp4".
    - By default, emptied split-part folders are left behind (harmless, just empty
      directories). Pass --delete-empty to clean them up after a successful merge.
"""

import argparse
import re
import shutil
import sys
from collections import defaultdict
from pathlib import Path

# Matches: "<Category Name>-20260701T104121Z-3-001"
SPLIT_PATTERN = re.compile(r"^(?P<category>.+)-\d{8}T\d{6}Z-\d+-\d+$")


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


def find_category_groups(root: Path):
    """Group split part-folders under root by their category name."""
    groups = defaultdict(list)
    for entry in sorted(root.iterdir()):
        if not entry.is_dir():
            continue
        match = SPLIT_PATTERN.match(entry.name)
        if match:
            category = match.group("category").strip()
            groups[category].append(entry)
    return groups


def merge_category(root: Path, category: str, parts, dry_run: bool, delete_empty: bool):
    dest_dir = root / category
    if not dry_run:
        dest_dir.mkdir(parents=True, exist_ok=True)

    moved_count = 0
    for part_folder in parts:
        subdirs = [d for d in part_folder.iterdir() if d.is_dir()]
        if len(subdirs) == 1:
            nested = subdirs[0]
        else:
            # Fall back to exact name match if there isn't exactly one subfolder.
            nested = part_folder / category
            if not nested.is_dir():
                print(f"Warning: could not find nested folder inside '{part_folder}', skipping part.", file=sys.stderr)
                continue

        for file_path in nested.rglob("*"):
            if not file_path.is_file():
                continue
            target = unique_target(dest_dir, file_path.name)
            if dry_run:
                print(f"[DRY RUN] Would move: {file_path} -> {target}")
            else:
                shutil.move(str(file_path), str(target))
                print(f"Moved: {file_path} -> {target}")
            moved_count += 1

        if delete_empty and not dry_run:
            # Remove now-empty nested folder and its part-folder, if truly empty.
            try:
                nested.rmdir()
                part_folder.rmdir()
                print(f"Removed emptied folder: {part_folder}")
            except OSError:
                pass  # not empty (unexpected extra files/folders) - leave it alone

    print(f"Category '{category}': {moved_count} file(s) {'would be ' if dry_run else ''}merged into {dest_dir}")


def main():
    parser = argparse.ArgumentParser(description="Merge Google Drive split-export category folders into one folder per category.")
    parser.add_argument("root", help="Root folder to scan (e.g. path to 'Drive-Data')")
    parser.add_argument("-c", "--category", help="Only merge this one category (default: all detected categories)")
    parser.add_argument("-n", "--dry-run", action="store_true", help="Preview actions without moving files")
    parser.add_argument("--delete-empty", action="store_true", help="Remove emptied split-part folders after merging")
    args = parser.parse_args()

    root = Path(args.root).expanduser()
    if not root.is_dir():
        print(f"Error: '{root}' is not a folder.", file=sys.stderr)
        sys.exit(1)

    groups = find_category_groups(root)
    if not groups:
        print("No split-export folders found (expected pattern: '<Category>-YYYYMMDDTHHMMSSZ-N-NNN').")
        return

    if args.category:
        if args.category not in groups:
            print(f"Error: category '{args.category}' not found. Available categories:", file=sys.stderr)
            for cat in sorted(groups):
                print(f"  - {cat}", file=sys.stderr)
            sys.exit(1)
        groups = {args.category: groups[args.category]}

    print(f"Found {len(groups)} categor{'y' if len(groups) == 1 else 'ies'} to merge:\n")
    for category, parts in sorted(groups.items()):
        print(f"=== {category} ({len(parts)} part folder(s)) ===")
        merge_category(root, category, parts, args.dry_run, args.delete_empty)
        print()

    print("Done.")


if __name__ == "__main__":
    main()
