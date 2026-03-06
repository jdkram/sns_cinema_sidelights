# author: Jonny Kram; ai-model: Claude Haiku; status: "#ai-input"
"""
record_sequences.py -- Generate asciinema recordings of all sequences

Creates a 20-second recording for each sequence (60 seconds for sparkle).
Recordings are saved to simulator/recordings/ as .cast files that can be
played back with `asciinema play`.

Does not require asciinema to be installed -- it writes .cast files directly
using Python's built-in pty module.

Usage:
    python3 simulator/record_sequences.py              # record all (takes ~5 min)
    python3 simulator/record_sequences.py heartbeat    # record one by name
    python3 simulator/record_sequences.py 3            # by button number
    python3 simulator/record_sequences.py --list       # show what will be recorded
"""

import argparse
import fcntl
import json
import os
import pty
import select
import signal
import struct
import sys
import termios
import time

# Allow running directly from the simulator/ directory or from project root.
sys.path.insert(0, os.path.dirname(__file__))

from sequences import SEQUENCES, BUTTON_MAP


def _get_recordings_dir() -> str:
    """Return path to simulator/recordings directory, creating if needed."""
    recordings_dir = os.path.join(os.path.dirname(__file__), "recordings")
    os.makedirs(recordings_dir, exist_ok=True)
    return recordings_dir


def _get_terminal_size() -> tuple[int, int]:
    """Return (cols, rows) of the current terminal, with a sensible fallback."""
    try:
        size = struct.unpack("HH", fcntl.ioctl(sys.stdout, termios.TIOCGWINSZ, b"\x00" * 4))
        rows, cols = size
        if cols > 0 and rows > 0:
            return cols, rows
    except Exception:
        pass
    return 220, 50


def _record_sequence(seq_name: str, duration: float) -> bool:
    """
    Record a single sequence directly to an asciinema v2 cast file.

    Spawns preview.py inside a PTY, reads all output with timestamps, and
    writes the cast file itself -- no dependency on the asciinema CLI.

    Returns True if successful, False otherwise.
    """
    if seq_name not in SEQUENCES:
        print(f"Error: sequence '{seq_name}' not found in SEQUENCES")
        return False

    recordings_dir = _get_recordings_dir()
    output_file = os.path.join(recordings_dir, f"{seq_name}.cast")
    cols, rows = _get_terminal_size()

    print(f"Recording '{seq_name}' for {duration:.0f}s... ", end="", flush=True)

    # Open a PTY pair
    master_fd, slave_fd = pty.openpty()

    # Set the PTY window size to match (or a fixed recording size)
    winsize = struct.pack("HHHH", rows, cols, 0, 0)
    fcntl.ioctl(slave_fd, termios.TIOCSWINSZ, winsize)

    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    pid = os.fork()
    if pid == 0:
        # Child: become a new session, attach to slave PTY, exec preview.py
        os.close(master_fd)
        os.setsid()
        fcntl.ioctl(slave_fd, termios.TIOCSCTTY, 0)
        os.dup2(slave_fd, 0)
        os.dup2(slave_fd, 1)
        os.dup2(slave_fd, 2)
        if slave_fd > 2:
            os.close(slave_fd)
        os.chdir(project_dir)
        os.execv(sys.executable, [sys.executable, "simulator/preview.py", seq_name])
        os._exit(1)

    # Parent: read from master, collect events
    os.close(slave_fd)
    events: list[list] = []
    start = time.monotonic()

    try:
        while True:
            elapsed = time.monotonic() - start
            if elapsed >= duration:
                break
            remaining = duration - elapsed
            rlist, _, _ = select.select([master_fd], [], [], min(0.02, remaining))
            if rlist:
                try:
                    data = os.read(master_fd, 4096)
                except OSError:
                    break  # child exited
                t = time.monotonic() - start
                events.append([round(t, 6), "o", data.decode("utf-8", errors="replace")])
    except KeyboardInterrupt:
        os.kill(pid, signal.SIGTERM)
        os.waitpid(pid, 0)
        os.close(master_fd)
        print("\nInterrupted.")
        return False

    os.kill(pid, signal.SIGTERM)
    os.waitpid(pid, 0)
    os.close(master_fd)

    if not events:
        print("failed (no output captured)")
        return False

    # Write asciinema v2 cast file
    header = {
        "version": 2,
        "width": cols,
        "height": rows,
        "timestamp": int(start),
        "title": seq_name,
        "env": {"TERM": "xterm-256color"},
    }
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(json.dumps(header) + "\n")
        for event in events:
            f.write(json.dumps(event) + "\n")

    file_size = os.path.getsize(output_file)
    print(f"done ({len(events)} frames, {file_size} bytes).")
    return True


def _find_agg_binary() -> str | None:
    """
    Return the path to the agg binary (agg or asciinema-agg), or None if not found.
    """
    import shutil
    for candidate in ("agg", "asciinema-agg"):
        path = shutil.which(candidate)
        if path:
            return path
    return None


def _cast_to_mp4(cast_file: str, mp4_file: str) -> bool:
    """
    Convert a .cast file to .mp4 via agg (cast -> gif) and ffmpeg (gif -> mp4).

    Tries both 'agg' and 'asciinema-agg' as the binary name.
    Requires ffmpeg to be installed.
    """
    import shutil
    import subprocess
    import tempfile

    seq_name = os.path.splitext(os.path.basename(cast_file))[0]
    print(f"  Converting '{seq_name}' to mp4... ", end="", flush=True)

    agg_bin = _find_agg_binary()
    if not agg_bin:
        print("failed ('agg' or 'asciinema-agg' not found)")
        print("    Install: snap install asciinema-agg OR download from github.com/asciinema/agg/releases")
        return False
    if not shutil.which("ffmpeg"):
        print("failed ('ffmpeg' not found)")
        print("    Install: sudo apt install ffmpeg")
        return False

    try:
        with tempfile.NamedTemporaryFile(suffix=".gif", delete=False) as tmp:
            gif_file = tmp.name

        # Always call as: agg_bin <input.cast> <output.gif>
        result = subprocess.run(
            [agg_bin, cast_file, gif_file],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"failed (agg: {result.stderr.strip()[:120]})")
            return False

        result = subprocess.run(
            ["ffmpeg", "-y", "-i", gif_file, "-movflags", "+faststart",
             "-pix_fmt", "yuv420p", "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
             mp4_file],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"failed (ffmpeg: {result.stderr.strip()[:120]})")
            return False

        file_size = os.path.getsize(mp4_file)
        print(f"done ({file_size} bytes).")
        return True
    except Exception as e:
        print(f"failed ({e})")
        return False
    finally:
        if os.path.exists(gif_file):
            os.unlink(gif_file)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Record asciinema demos of SNS sidelight sequences.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="\n".join([
            "Examples:",
            "  python3 simulator/record_sequences.py                           # record all",
            "  python3 simulator/record_sequences.py heartbeat                 # by name",
            "  python3 simulator/record_sequences.py 3                         # by button number",
            "  python3 simulator/record_sequences.py --list                    # show what will be recorded",
            "  python3 simulator/record_sequences.py --export-mp4              # convert all existing .cast files",
            "  python3 simulator/record_sequences.py heartbeat --export-mp4   # record then convert",
        ]),
    )
    parser.add_argument(
        "sequence",
        nargs="?",
        help="Sequence name (e.g. heartbeat) or button number (1-15).",
    )
    parser.add_argument(
        "--list", action="store_true",
        help="List sequences that will be recorded and exit.",
    )
    parser.add_argument(
        "--export-mp4", action="store_true",
        help="Convert .cast files to .mp4 after recording. If no sequence is specified, converts all existing .cast files without re-recording.",
    )
    args = parser.parse_args()

    # Define recording durations: sparkle is 60s, others are 20s
    durations = {
        "sparkle": 60.0,
    }
    default_duration = 20.0

    if args.list:
        print("\nSequences to record:\n")
        for name in sorted(SEQUENCES.keys()):
            duration = durations.get(name, default_duration)
            button = next((b for b, n in BUTTON_MAP.items() if n == name), "-")
            print(f"  {name:<14s} (button {button:2s})  {duration:.0f}s")
        print()
        return

    # --export-mp4 with no sequence: convert all existing .cast files, skip recording
    if args.export_mp4 and not args.sequence:
        recordings_dir = _get_recordings_dir()
        cast_files = sorted(f for f in os.listdir(recordings_dir) if f.endswith(".cast"))
        if not cast_files:
            print("No .cast files found in recordings/.")
            sys.exit(1)
        print(f"\nConverting {len(cast_files)} existing .cast file(s) to mp4...\n")
        succeeded = 0
        failed = 0
        for cast_filename in cast_files:
            cast_path = os.path.join(recordings_dir, cast_filename)
            mp4_path = os.path.join(recordings_dir, cast_filename.replace(".cast", ".mp4"))
            if _cast_to_mp4(cast_path, mp4_path):
                succeeded += 1
            else:
                failed += 1
        print(f"\nDone: {succeeded} succeeded, {failed} failed.")
        sys.exit(0 if failed == 0 else 1)

    # Determine which sequences to record
    if args.sequence:
        # Single sequence specified
        if args.sequence in SEQUENCES:
            sequences_to_record = [args.sequence]
        else:
            # Try to resolve as button number
            try:
                button = int(args.sequence)
                if button in BUTTON_MAP:
                    sequences_to_record = [BUTTON_MAP[button]]
                else:
                    print(f"Unknown button {button}. Use --list to see available sequences.", file=sys.stderr)
                    sys.exit(1)
            except ValueError:
                print(f"Unknown sequence '{args.sequence}'. Use --list to see available sequences.", file=sys.stderr)
                sys.exit(1)
    else:
        # Record all sequences
        sequences_to_record = sorted(SEQUENCES.keys())

    print()
    total_duration = sum(durations.get(name, default_duration) for name in sequences_to_record)
    print(f"Will record {len(sequences_to_record)} sequence(s) (~{total_duration / 60:.1f} minutes total)\n")

    recordings_dir = _get_recordings_dir()
    print(f"Saving to: {recordings_dir}\n")

    # Record each sequence
    succeeded = 0
    failed = 0
    try:
        for seq_name in sequences_to_record:
            duration = durations.get(seq_name, default_duration)
            recorded = _record_sequence(seq_name, duration)
            if recorded and args.export_mp4:
                cast_path = os.path.join(recordings_dir, f"{seq_name}.cast")
                mp4_path = os.path.join(recordings_dir, f"{seq_name}.mp4")
                recorded = _cast_to_mp4(cast_path, mp4_path)
            if recorded:
                succeeded += 1
            else:
                failed += 1
    except KeyboardInterrupt:
        print("\n\nRecording interrupted by user.")
        sys.exit(1)

    print(f"\nDone: {succeeded} succeeded, {failed} failed.")
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
