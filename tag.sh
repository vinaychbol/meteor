#!/usr/bin/env bash
# tag.sh - bump pyproject.toml semantic version and create a git tag
# Usage: ./tag.sh [patch|minor|major]    (default: patch)

set -euo pipefail

FILE="pyproject.toml"
BUMP="${1:-patch}"   # patch, minor, or major
TAG_PREFIX="v"       # prefix for the git tag, set to "" if you don't want 'v'

if [[ ! -f "$FILE" ]]; then
    echo "Error: $FILE not found in $(pwd)" >&2
    exit 1
fi

# Ensure we are in a git repo and working tree is clean
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "Error: not inside a git repository" >&2
    exit 1
fi

if ! git diff-index --quiet HEAD --; then
    echo "Error: working tree has uncommitted changes. Commit or stash them first." >&2
    exit 1
fi

# Extract the first semantic version like 1.2.3 from pyproject.toml (version = "1.2.3")
current_version_line=$(grep -m1 -E '^\s*version\s*=\s*"[0-9]+\.[0-9]+\.[0-9]+"' "$FILE" || true)
if [[ -z "$current_version_line" ]]; then
    # try a more portable grep (in case grep doesn't support -E in some environments)
    current_version_line=$(grep -m1 'version' "$FILE" || true)
fi

current_version=$(printf '%s' "$current_version_line" | sed -nE 's/.*version\s*=\s*"[[:space:]]*([0-9]+\.[0-9]+\.[0-9]+)[[:space:]]*".*/\1/p' || true)

if [[ -z "$current_version" ]]; then
    echo "Error: could not find a semantic version (X.Y.Z) in $FILE" >&2
    exit 1
fi

# Split into components
IFS='.' read -r major minor patch <<< "$current_version"
if [[ -z "$major" || -z "$minor" || -z "$patch" ]]; then
    echo "Error: parsed version is invalid: $current_version" >&2
    exit 1
fi

case "$BUMP" in
    major)
        major=$((major + 1))
        minor=0
        patch=0
        ;;
    minor)
        minor=$((minor + 1))
        patch=0
        ;;
    patch)
        patch=$((patch + 1))
        ;;
    *)
        echo "Error: unknown bump type '$BUMP'. Use patch, minor, or major." >&2
        exit 1
        ;;
esac

new_version="${major}.${minor}.${patch}"
tag_name="${TAG_PREFIX}${new_version}"

# Ensure tag doesn't already exist
if git rev-parse -q --verify "refs/tags/${tag_name}" >/dev/null 2>&1; then
    echo "Error: tag '${tag_name}' already exists" >&2
    exit 1
fi

# Update only the first occurrence of version = "X.Y.Z" in the file
tmpfile="$(mktemp "${TMPDIR:-/tmp}/pyproject.XXXXXX")"
awk -v nv="$new_version" '
BEGIN{replaced=0}
{
    if(!replaced && $0 ~ /version[[:space:]]*=[[:space:]]*"[0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*"/) {
        sub(/"[0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*"/, "\"" nv "\"")
        replaced=1
    }
    print
}
' "$FILE" > "$tmpfile"

# If awk didn't replace anything, abort
if ! diff -q "$FILE" "$tmpfile" >/dev/null 2>&1; then
    mv "$tmpfile" "$FILE"
else
    rm -f "$tmpfile"
    echo "Error: failed to update version in $FILE" >&2
    exit 1
fi

# Commit and tag
git add "$FILE"
git commit -m "Bump version to ${tag_name}"
git tag -a "$tag_name" -m "$tag_name"

echo "Version bumped: ${current_version} -> ${new_version}"
echo "Created git tag: ${tag_name}"