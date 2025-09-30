import json
import random
import time
import sys
import tty
import termios
import os
from datetime import timedelta
from collections import defaultdict

# ANSI color codes - using standard codes for compatibility
class Colors:
    WHITE = '\033[0m\033[97m'  # Bright white text
    GREEN = '\033[0m\033[92m'  # Bright green text
    RED = '\033[0m\033[91m'  # Bright red text
    YELLOW = '\033[0m\033[93m'  # Bright yellow text
    DIM = '\033[0m\033[90m'  # Bright black (gray) text
    ORANGE = '\033[0m\033[33m'  # Yellow (closest to orange in standard ANSI)

    # Backgrounds
    BG_RED = '\033[41m'  # Red background
    BG_ORANGE = '\033[43m'  # Yellow background (closest to orange)
    BG_CLEAR = '\033[49m'  # Clear background

    # Special combinations
    CURSOR_HIGHLIGHT = '\033[0m\033[43m\033[30m'  # Yellow bg + black text
    ERROR_HIGHLIGHT = '\033[0m\033[41m\033[97m'  # Red bg + bright white text

def clear_screen():
    print('\033[2J\033[H\033[0m\033[97m', end='')  # Clear screen, reset, set bright white text

def get_terminal_height():
    """Get the terminal height in lines."""
    return os.get_terminal_size().lines

def load_random_problem(filename='problems.json'):
    """Load a random problem from the JSON file."""
    with open(filename, 'r') as f:
        data = json.load(f)
    # Filter out empty problem lists
    data = [p for p in data if p and len(p) > 0]
    if not data:
        raise ValueError("No valid problems found in JSON file")
    problem_list = random.choice(data)
    problem = problem_list[0]
    return problem['id'], problem['code']

def get_char():
    """Get a single character from stdin without waiting for Enter."""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        char = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return char

def display_header(problem_id):
    """Display the header with problem information."""
    print(f"{Colors.ORANGE}{'='*80}")
    print(f"{Colors.ORANGE}TYPING SPEED TEST")
    print(f"{Colors.ORANGE}{'='*80}")
    print(f"{Colors.YELLOW}Problem: {problem_id}")
    print(f"{Colors.DIM}Type the code below. Press Ctrl+C to quit.\n")

def calculate_scroll_window(target_text, current_pos, terminal_height):
    """Calculate which lines to display based on cursor position for smooth scrolling."""
    lines = target_text.split('\n')

    # Reserve lines for header (5 lines)
    header_lines = 5
    available_lines = terminal_height - header_lines

    # Find which line the cursor is on
    char_count = 0
    cursor_line = 0
    for line_idx, line in enumerate(lines):
        if char_count + len(line) >= current_pos:
            cursor_line = line_idx
            break
        char_count += len(line) + 1  # +1 for newline

    # Calculate the window with cursor roughly in the middle
    center_offset = available_lines // 2
    start_line = max(0, cursor_line - center_offset)
    end_line = min(len(lines), start_line + available_lines)

    # Adjust if we're at the end
    if end_line == len(lines):
        start_line = max(0, end_line - available_lines)

    return start_line, end_line

def display_text_with_cursor(target_text, typed_text, current_pos):
    """Display the target text with color-coded typed characters and cursor."""
    print('\033[H\033[J', end='')  # Clear screen and move to top

    lines = target_text.split('\n')
    terminal_height = get_terminal_height()
    start_line, end_line = calculate_scroll_window(target_text, current_pos, terminal_height)

    char_count = 0
    # Calculate char_count offset for start_line
    for i in range(start_line):
        char_count += len(lines[i]) + 1  # +1 for newline

    for line_idx in range(start_line, end_line):
        line = lines[line_idx]
        output = ""
        for char_idx, char in enumerate(line):
            abs_pos = char_count + char_idx

            # Convert tabs to 8 spaces for display
            display_char = '        ' if char == '\t' else char

            if abs_pos < len(typed_text):
                if typed_text[abs_pos] == char:
                    output += f"{Colors.WHITE}{display_char}"  # Correct chars are white
                else:
                    # Show the incorrect character with red highlight
                    wrong_char = typed_text[abs_pos]
                    display_wrong = '        ' if wrong_char == '\t' else ('·' if wrong_char == ' ' else wrong_char)
                    output += f"{Colors.ERROR_HIGHLIGHT}{display_wrong}"
            elif abs_pos == current_pos:
                # Highlight current character cell with background (orange background + black text)
                if char == ' ':
                    # For spaces, show highlighted block
                    output += f"{Colors.CURSOR_HIGHLIGHT} "
                else:
                    output += f"{Colors.CURSOR_HIGHLIGHT}{display_char}"
            else:
                output += f"{Colors.DIM}{display_char}"

        # Check if cursor is at end of line (one position after last char)
        end_of_line_pos = char_count + len(line)
        if end_of_line_pos == current_pos and line_idx < len(lines) - 1:
            # Show cursor at end of line for Enter key (orange background + black text)
            output += f"{Colors.CURSOR_HIGHLIGHT}↵"

        print(output + Colors.WHITE)
        char_count += len(line)


        # Account for newline character
        if line_idx < len(lines) - 1:
            if char_count < len(typed_text):

                pass
            elif char_count == current_pos:
                #print(f"\033[48;2;222;157;105m{Colors.BOLD}↵\033[0m")  # Highlight newline with background
                pass
            else:
                pass

            char_count += 1

def calculate_metrics(target_text, typed_text, elapsed_time, all_typed_chars, wrong_typed_chars):
    """Calculate typing metrics."""
    total_chars = len(target_text)
    typed_chars = len(typed_text)
    correct_chars = sum(1 for i, c in enumerate(typed_text) if i < len(target_text) and c == target_text[i])

    minutes = elapsed_time / 60
    # WPM: ((ALL TYPED CHARS / 5) - wrong typed chars) / Time in minutes
    accuracy = (correct_chars / all_typed_chars * 100) if all_typed_chars > 0 else 0
    wpm = ((all_typed_chars - wrong_typed_chars) / 5) / minutes * accuracy / 100 if minutes > 0 else 0

    return {
        'total_chars': total_chars,
        'typed_chars': typed_chars,
        'correct_chars': correct_chars,
        'all_typed_chars': all_typed_chars,
        'wrong_typed_chars': wrong_typed_chars,
        'wpm': wpm,
        'accuracy': accuracy,
        'time': elapsed_time
    }

def display_results(metrics, missed_chars):
    """Display final results."""
    clear_screen()
    print(f"{Colors.ORANGE}{'='*80}")
    print(f"{Colors.ORANGE}RESULTS")
    print(f"{Colors.ORANGE}{'='*80}")
    print(f"{Colors.WHITE}Time Elapsed: {timedelta(seconds=int(metrics['time']))}")
    print(f"{Colors.WHITE}Words Per Minute (WPM): {Colors.GREEN}{metrics['wpm']:.1f}")
    print(f"{Colors.WHITE}Accuracy: {Colors.GREEN if metrics['accuracy'] >= 95 else Colors.YELLOW}{metrics['accuracy']:.1f}%")
    print(f"{Colors.WHITE}Character Breakdown:")
    print(f"{Colors.WHITE}  Target Characters: {metrics['total_chars']}")
    print(f"{Colors.WHITE}  {Colors.GREEN}Correct: {metrics['correct_chars']}")
    print(f"{Colors.WHITE}  {Colors.RED}Wrong: {metrics['wrong_typed_chars']}")
    print(f"{Colors.WHITE}  Total Typed: {metrics['all_typed_chars']}")

    if missed_chars:
        print(f"\n{Colors.WHITE}Most Missed Characters:")
        sorted_missed = sorted(missed_chars.items(), key=lambda x: x[1], reverse=True)
        for char, count in sorted_missed[:10]:  # Show top 10
            display_char = repr(char) if char in ('\n', '\t', ' ') else char
            print(f"{Colors.WHITE}  {Colors.RED}{display_char}: {count}")

    print(f"{Colors.ORANGE}{'='*80}")

def main():
    try:
        # Load problem
        problem_id, target_text = load_random_problem()

        clear_screen()
        display_header(problem_id)

        # Initialize
        typed_text = ""
        start_time = None  # Will start on first key press
        current_pos = 0
        all_typed_chars = 0  # Track all characters typed including deleted ones
        wrong_typed_chars = 0  # Track characters that were typed incorrectly
        missed_chars = defaultdict(int)  # Track which characters were missed

        clear_screen()
        display_header(problem_id)
        # Main typing loop
        while current_pos < len(target_text):
            display_header(problem_id)
            display_text_with_cursor(target_text, typed_text, current_pos)

            char = get_char()

            # Start timer on first keypress
            if start_time is None:
                start_time = time.time()

            # Handle special keys
            if ord(char) == 3:  # Ctrl+C
                raise KeyboardInterrupt
            elif ord(char) == 127:  # Backspace
                if typed_text:
                    typed_text = typed_text[:-1]
                    current_pos = max(0, current_pos - 1)
            elif char == '\t':  # Tab key
                typed_text += '  '  # Insert 2 spaces
                all_typed_chars += 2
                # Check if these characters are correct
                for i in range(current_pos, min(current_pos + 2, len(target_text))):
                    if i >= len(target_text) or typed_text[i] != target_text[i]:
                        wrong_typed_chars += 1
                        if i < len(target_text):
                            missed_chars[target_text[i]] += 1
                current_pos += 2
            elif char == '\n' or char == '\r':  # Enter key - autoindent
                # Find the start of the current line in target_text
                target_line_start = target_text.rfind('\n', 0, current_pos) + 1
                target_line = target_text[target_line_start:target_text.find('\n', target_line_start) if '\n' in target_text[target_line_start:] else len(target_text)]

                # Count leading whitespace (tabs and spaces) in current line
                current_indent = ''
                for c in target_line:
                    if c in ('\t', ' '):
                        current_indent += c
                    else:
                        break

                # Find next line's indentation
                next_line_start = current_pos + 1
                next_line_end = target_text.find('\n', next_line_start) if '\n' in target_text[next_line_start:] else len(target_text)
                next_line = target_text[next_line_start:next_line_end]

                next_indent = ''
                for c in next_line:
                    if c in ('\t', ' '):
                        next_indent += c
                    else:
                        break

                # If next line has less indentation, just skip to next char (newline only)
                # Otherwise use current line's indentation
                if len(next_indent) < len(current_indent):
                    typed_text += '\n'
                    all_typed_chars += 1
                    if current_pos >= len(target_text) or typed_text[current_pos] != target_text[current_pos]:
                        wrong_typed_chars += 1
                        if current_pos < len(target_text):
                            missed_chars[target_text[current_pos]] += 1
                    current_pos += 1
                else:
                    indent_to_add = '\n' + current_indent
                    typed_text += indent_to_add
                    all_typed_chars += len(indent_to_add)
                    # Check if these characters are correct
                    for i in range(current_pos, min(current_pos + len(indent_to_add), len(target_text))):
                        if i >= len(target_text) or typed_text[i] != target_text[i]:
                            wrong_typed_chars += 1
                            if i < len(target_text):
                                missed_chars[target_text[i]] += 1
                    current_pos += len(indent_to_add)
            else:
                typed_text += char
                all_typed_chars += 1
                # Check if this character is correct
                if current_pos >= len(target_text) or char != target_text[current_pos]:
                    wrong_typed_chars += 1
                    if current_pos < len(target_text):
                        missed_chars[target_text[current_pos]] += 1
                current_pos += 1

        # Calculate elapsed time
        elapsed_time = time.time() - start_time

        # Calculate and display metrics
        metrics = calculate_metrics(target_text, typed_text, elapsed_time, all_typed_chars, wrong_typed_chars)
        display_results(metrics, missed_chars)

    except KeyboardInterrupt:
        print(f"{Colors.YELLOW}Test cancelled.")
        sys.exit(0)
    except FileNotFoundError:
        print(f"{Colors.RED}Error: problems.json not found!")
        sys.exit(1)
    except Exception as e:
        print(f"{Colors.RED}Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()