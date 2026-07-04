#!/bin/bash
#
# move_files.sh - Move (cut & paste) files from multiple source folders into one destination folder.
#
# Usage:
#   ./move_files.sh [-r] [-n] -d <destination_folder> <source_folder1> [source_folder2] ...
#
# Options:
#   -d DIR   Destination folder (required). Created if it doesn't exist.
#   -r       Recursive - also move files from subfolders of each source.
#   -n       Dry run - show what would be moved without actually moving anything.
#
# Examples:
#   ./move_files.sh -d ~/Desktop/AllPhotos ~/Desktop/Camera1 ~/Desktop/Camera2
#   ./move_files.sh -r -n -d ~/Desktop/AllDocs ~/Desktop/Folder1 ~/Desktop/Folder2 ~/Desktop/Folder3
#
# Notes:
#   - If a file with the same name already exists in the destination, this script
#     will NOT overwrite it. Instead it appends a number, e.g. "photo.jpg" -> "photo (1).jpg".
#   - Only files are moved; empty source folders are left behind (not deleted).

set -euo pipefail

usage() {
    echo "Usage: $0 [-r] [-n] -d <destination_folder> <source_folder1> [source_folder2] ..."
    echo
    echo "  -d DIR   Destination folder (required)"
    echo "  -r       Recursive - include files in subfolders of each source"
    echo "  -n       Dry run - preview actions without moving files"
    exit 1
}

DEST=""
RECURSIVE=0
DRY_RUN=0

while getopts ":d:rn" opt; do
    case "$opt" in
        d) DEST="$OPTARG" ;;
        r) RECURSIVE=1 ;;
        n) DRY_RUN=1 ;;
        *) usage ;;
    esac
done
shift $((OPTIND - 1))

if [[ -z "$DEST" ]]; then
    echo "Error: destination folder (-d) is required." >&2
    usage
fi

if [[ $# -eq 0 ]]; then
    echo "Error: at least one source folder is required." >&2
    usage
fi

# Resolve destination to an absolute path and create it if needed.
if [[ $DRY_RUN -eq 0 ]]; then
    mkdir -p "$DEST"
fi
DEST="$(cd "$DEST" 2>/dev/null && pwd || echo "$DEST")"

move_one_file() {
    local src_file="$1"
    local filename
    filename="$(basename "$src_file")"
    local target="$DEST/$filename"

    # Avoid moving a file onto itself if source == destination.
    if [[ "$(cd "$(dirname "$src_file")" && pwd)" == "$DEST" ]]; then
        return
    fi

    # If a file with the same name exists, append a counter to avoid overwriting.
    if [[ -e "$target" ]]; then
        local name="${filename%.*}"
        local ext="${filename##*.}"
        local counter=1
        if [[ "$name" == "$ext" ]]; then
            # No extension case
            target="$DEST/${filename} ($counter)"
            while [[ -e "$target" ]]; do
                counter=$((counter + 1))
                target="$DEST/${filename} ($counter)"
            done
        else
            target="$DEST/${name} ($counter).${ext}"
            while [[ -e "$target" ]]; do
                counter=$((counter + 1))
                target="$DEST/${name} ($counter).${ext}"
            done
        fi
    fi

    if [[ $DRY_RUN -eq 1 ]]; then
        echo "[DRY RUN] Would move: $src_file -> $target"
    else
        mv "$src_file" "$target"
        echo "Moved: $src_file -> $target"
    fi
}

for src in "$@"; do
    if [[ ! -d "$src" ]]; then
        echo "Warning: '$src' is not a folder, skipping." >&2
        continue
    fi

    if [[ $RECURSIVE -eq 1 ]]; then
        find "$src" -type f -print0
    else
        find "$src" -maxdepth 1 -type f -print0
    fi | while IFS= read -r -d '' file; do
        move_one_file "$file"
    done
done

echo "Done."
