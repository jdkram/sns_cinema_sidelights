# author: Jonny Kram; ai-model: Claude Haiku; status: "#ai-input"
"""
upload_casts.py -- Upload all .cast files in ./simulator/recordings to asciinema.org

Outputs a list of sequences and their asciinema URLs in the format:
    sequence - https://asciinema.org/a/XXXXX

First, ensure you're logged in:
    asciinema auth

Usage:
    python3 simulator/upload_casts.py
"""

import os
import re
import subprocess
import sys


def _get_recordings_dir() -> str:
    """Return path to simulator/recordings directory."""
    recordings_dir = os.path.join(os.path.dirname(__file__), "recordings")
    return recordings_dir


def _upload_cast(cast_file: str) -> str | None:
    """
    Upload a single .cast file and return its asciinema URL, or None on failure.
    
    Parses the output of `asciinema upload` to extract the URL.
    """
    seq_name = os.path.splitext(os.path.basename(cast_file))[0]
    print(f"Uploading '{seq_name}'... ", end="", flush=True)
    
    try:
        result = subprocess.run(
            ["asciinema", "upload", cast_file],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            print(f"failed ({result.stderr.strip()[:80]})")
            return None
        
        # Look for URL in output (from stdout or stderr)
        output = result.stdout + result.stderr
        matches = re.findall(r"https://asciinema\.org/a/[\w]+", output)
        
        if matches:
            url = matches[0]
            print(f"done")
            return url
        else:
            # Fallback: look for any asciinema.org URL
            matches = re.findall(r"https://[^\s]+asciinema[^\s]+", output)
            if matches:
                url = matches[0]
                print(f"done")
                return url
            
            print(f"failed (no URL found in output)")
            print(f"  stdout: {result.stdout[:200]}")
            print(f"  stderr: {result.stderr[:200]}")
            return None
    except subprocess.TimeoutExpired:
        print("failed (timeout)")
        return None
    except Exception as e:
        print(f"failed ({e})")
        return None


def main() -> None:
    recordings_dir = _get_recordings_dir()
    
    if not os.path.isdir(recordings_dir):
        print(f"Error: {recordings_dir} not found")
        sys.exit(1)
    
    # Find all .cast files
    cast_files = sorted([
        f for f in os.listdir(recordings_dir)
        if f.endswith(".cast")
    ])
    
    if not cast_files:
        print("No .cast files found in recordings/")
        sys.exit(1)
    
    print(f"\nUploading {len(cast_files)} .cast file(s) to asciinema.org\n")
    
    results = []
    for cast_filename in cast_files:
        cast_path = os.path.join(recordings_dir, cast_filename)
        url = _upload_cast(cast_path)
        if url:
            seq_name = os.path.splitext(cast_filename)[0]
            results.append((seq_name, url))
    
    # Print results
    print(f"\n{'─' * 70}")
    print(f"Upload complete: {len(results)}/{len(cast_files)} succeeded\n")
    
    for seq_name, url in results:
        print(f"{seq_name} - {url}")
    
    print()
    
    if len(results) < len(cast_files):
        sys.exit(1)


if __name__ == "__main__":
    main()
