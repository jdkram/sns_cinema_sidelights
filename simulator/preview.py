# ai-input
"""
preview.py -- terminal renderer for light sequence simulation

Renders all 24 LEDs with the physical layout: left bank (3 per row) on the
left, cinema screen in the middle, right bank (3 per row) on the right.
Updates at ~30 fps with warm amber colouring that brightens as brightness
increases.

Press 1-5 during playback to instantly switch to another sequence. Press Ctrl+C
to exit.

Requires a terminal that supports ANSI true-colour (most modern terminals
on Linux, macOS, and Windows Terminal do).

Usage:
    python3 simulator/preview.py                  # interactive picker
    python3 simulator/preview.py heartbeat        # by name
    python3 simulator/preview.py 3                # by button number
    python3 simulator/preview.py --list           # show available sequences

See sequences.py to add a new sequence.
"""

import argparse
import os
import select
import sys
import termios
import time
import tty

# Allow running directly from the simulator/ directory or from project root.
sys.path.insert(0, os.path.dirname(__file__))

from engine import LEDManager
from sequences import SEQUENCES, BUTTON_MAP


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

LEDS_PER_SIDE = 3     # LEDs per half-row (left bank or right bank)
_SCREEN_LABEL = "  [ SCREEN ]  "   # 14 visible chars; sits between the two banks
# 1 header + 1 separator + 4 LED rows + 1 separator + 1 sequence line + 1 instructions
_FRAME_LINES = 9

# Warm amber colour endpoints for brightness 0..100
_OFF  = (10,   5,  0)
_FULL = (255, 160, 10)


def _lerp(a: int, b: int, t: float) -> int:
    return int(a + (b - a) * t)


def _led_block(led_num: int, brightness: float) -> str:
    """Return an ANSI-coloured 5-char block representing one LED."""
    t = max(0.0, min(1.0, brightness / 100.0))
    r = _lerp(_OFF[0], _FULL[0], t)
    g = _lerp(_OFF[1], _FULL[1], t)
    b = _lerp(_OFF[2], _FULL[2], t)
    text = "\033[38;2;200;100;0m" if brightness < 50 else "\033[38;2;30;15;0m"
    return f"\033[48;2;{r};{g};{b}m{text} {led_num:02d}  \033[0m"


def _render_frame(state: list[float], seq_name: str, elapsed: float, first: bool) -> None:
    """Print the full display, overwriting the previous frame in-place."""
    rows: list[str] = []

    # Separator width = two banks of 3 LEDs (5 chars each) + screen label
    sep_width = LEDS_PER_SIDE * 5 * 2 + len(_SCREEN_LABEL)
    separator = "─" * sep_width
    rows.append("SNS Sidelight Simulator")
    rows.append(separator)

    for row_num in range(4):
        base = row_num * 6  # first LED index (0-based) for this row
        left  = "".join(_led_block(base + i + 1, state[base + i])           for i in range(LEDS_PER_SIDE))
        right = "".join(_led_block(base + LEDS_PER_SIDE + i + 1, state[base + LEDS_PER_SIDE + i]) for i in range(LEDS_PER_SIDE))
        rows.append(left + _SCREEN_LABEL + right)

    rows.append(separator)

    mins = int(elapsed) // 60
    secs = int(elapsed) % 60
    rows.append(f"Sequence: {seq_name:<12s}  Elapsed: {mins}:{secs:02d}")
    max_button = max(BUTTON_MAP.keys()) if BUTTON_MAP else 5
    rows.append(f"Press 1-{max_button} to switch sequence, or Ctrl+C to quit")

    if not first:
        # Move up N lines and return to column 0.
        # \r is required because tty.setraw() is active and \n alone is a bare
        # line feed (no carriage return), so the cursor would stay at a non-zero
        # column without the explicit \r.
        sys.stdout.write(f"\033[{_FRAME_LINES}A\r")

    # Use \r\n for the same reason: in raw mode \n does not imply \r.
    sys.stdout.write("\r\n".join(rows) + "\r\n")
    sys.stdout.flush()


# ---------------------------------------------------------------------------
# Terminal input handling
# ---------------------------------------------------------------------------

_ORIGINAL_TERMINAL_SETTINGS = None


def _setup_terminal() -> None:
    """Set stdin to raw, non-blocking mode for single-key input."""
    global _ORIGINAL_TERMINAL_SETTINGS
    fd = sys.stdin.fileno()
    _ORIGINAL_TERMINAL_SETTINGS = termios.tcgetattr(fd)
    tty.setraw(fd)


def _restore_terminal() -> None:
    """Restore terminal to original settings."""
    if _ORIGINAL_TERMINAL_SETTINGS:
        fd = sys.stdin.fileno()
        termios.tcsetattr(fd, termios.TCSADRAIN, _ORIGINAL_TERMINAL_SETTINGS)


def _read_key_nonblocking() -> str | None:
    """Return a single key press if available, None otherwise."""
    if select.select([sys.stdin], [], [], 0)[0]:
        try:
            return sys.stdin.read(1)
        except:
            return None
    return None


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def run(initial_seq_name: str, fps: int = 30) -> None:
    seq_name = initial_seq_name
    led_manager = LEDManager()

    seq_class = SEQUENCES[seq_name]
    print(f"\nBuilding sequence '{seq_name}'... ", end="", flush=True)
    seq = seq_class(led_manager)
    print("done.\n")

    seq.start()
    frame_interval = 1.0 / fps
    first = True
    input_buffer = ""
    last_input_time = None
    input_timeout = 0.5  # seconds before executing buffered input

    try:
        while True:
            frame_start = time.monotonic()
            
            # Check for timeout on buffered input
            if input_buffer and last_input_time:
                if time.monotonic() - last_input_time > input_timeout:
                    try:
                        button_num = int(input_buffer)
                        if button_num in BUTTON_MAP:
                            new_seq_name = BUTTON_MAP[button_num]
                            if new_seq_name != seq_name:
                                seq_name = new_seq_name
                                led_manager.reset_all()
                                seq_class = SEQUENCES[seq_name]
                                seq = seq_class(led_manager)
                                seq.start()
                                first = True
                    except ValueError:
                        pass
                    input_buffer = ""
                    last_input_time = None
            
            seq.update()
            _render_frame(led_manager.state(), seq_name, seq.elapsed_seconds(), first)
            first = False

            # Check for keypresses while waiting for next frame
            while True:
                key = _read_key_nonblocking()
                if key is None:
                    break
                if key == '\x03':  # Ctrl+C
                    raise KeyboardInterrupt
                if key.isdigit():
                    input_buffer += key
                    last_input_time = time.monotonic()
                    button_num = int(input_buffer)
                    
                    # Check if this button exists
                    if button_num in BUTTON_MAP:
                        # Check if any valid button in BUTTON_MAP could start with (button_num * 10)
                        # i.e., is there a button in [button_num * 10, button_num * 10 + 9]?
                        has_continuation = any(
                            button_num * 10 <= b < button_num * 10 + 10
                            for b in BUTTON_MAP.keys()
                        )
                        
                        if not has_continuation:
                            # No valid continuation, execute immediately
                            new_seq_name = BUTTON_MAP[button_num]
                            if new_seq_name != seq_name:
                                seq_name = new_seq_name
                                led_manager.reset_all()
                                seq_class = SEQUENCES[seq_name]
                                seq = seq_class(led_manager)
                                seq.start()
                                first = True
                            input_buffer = ""
                            last_input_time = None
                            break
                    else:
                        # Invalid button, clear buffer and discard
                        input_buffer = ""
                        last_input_time = None

            elapsed = time.monotonic() - frame_start
            sleep = frame_interval - elapsed
            if sleep > 0:
                time.sleep(sleep)
    except KeyboardInterrupt:
        print("\n\nStopped.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _pick_interactively() -> str:
    """Show a numbered menu and return the chosen sequence name."""
    print("\nAvailable sequences:\n")
    names = list(SEQUENCES.keys())
    for i, name in enumerate(names, 1):
        button = next((b for b, n in BUTTON_MAP.items() if n == name), "-")
        docstring_first_line = (SEQUENCES[name].__doc__ or "").strip().splitlines()[0]
        print(f"  {i}. {name:<14s} (button {button})  {docstring_first_line}")
    print()
    while True:
        raw = input("Enter number or name: ").strip().lower()
        if raw in SEQUENCES:
            return raw
        try:
            index = int(raw) - 1
            if 0 <= index < len(names):
                return names[index]
        except ValueError:
            pass
        print(f"  Not recognised. Enter a number 1-{len(names)} or a sequence name.")


def _resolve(arg: str) -> str:
    """Resolve a CLI argument (name or button number) to a sequence name."""
    if arg in SEQUENCES:
        return arg
    try:
        button = int(arg)
        if button in BUTTON_MAP:
            return BUTTON_MAP[button]
    except ValueError:
        pass
    print(f"Unknown sequence '{arg}'. Use --list to see available sequences.", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Preview SNS sidelight sequences in the terminal.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="\n".join([
            "Examples:",
            "  python3 simulator/preview.py                 # interactive picker",
            "  python3 simulator/preview.py heartbeat       # by name",
            "  python3 simulator/preview.py 3               # by button number",
            "  python3 simulator/preview.py --list          # show all sequences",
        ]),
    )
    parser.add_argument(
        "sequence",
        nargs="?",
        help="Sequence name (e.g. heartbeat) or button number (1-5).",
    )
    parser.add_argument(
        "--list", action="store_true",
        help="List available sequences and exit.",
    )
    parser.add_argument(
        "--fps", type=int, default=30,
        help="Render frames per second (default: 30).",
    )
    args = parser.parse_args()

    if args.list:
        print("\nAvailable sequences:\n")
        for name, cls in SEQUENCES.items():
            button = next((b for b, n in BUTTON_MAP.items() if n == name), "-")
            first_line = (cls.__doc__ or "").strip().splitlines()[0]
            print(f"  button {button}  {name:<14s}  {first_line}")
        print()
        return

    if args.sequence:
        seq_name = _resolve(args.sequence)
    else:
        seq_name = _pick_interactively()

    _setup_terminal()
    try:
        run(seq_name, fps=args.fps)
    finally:
        _restore_terminal()


if __name__ == "__main__":
    main()
