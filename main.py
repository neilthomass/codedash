#!/usr/bin/env python3
import json
import random
import time
import sys
import tty
import termios
from datetime import timedelta

# ANSI color codes
class Colors:
    RESET = '\033[0m'
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ORANGE = '\033[38;2;222;157;105m'  # Claude tan-orange highlight

def clear_screen():
    print('\033[2J\033[H', end='')

def load_random_problem(filename='problems.json'):
    """Load a random problem from the JSON file."""
    with open(filename, 'r') as f:
        data = json.load(f)
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
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}TYPING SPEED TEST{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*80}{Colors.RESET}")
    print(f"{Colors.YELLOW}Problem: {problem_id}{Colors.RESET}")
    print(f"{Colors.DIM}Type the code below. Press Ctrl+C to quit.{Colors.RESET}\n")

def display_text_with_cursor(target_text, typed_text, current_pos):
    """Display the target text with color-coded typed characters and cursor."""
    print('\033[H\033[J', end='')  # Clear screen and move to top

    lines = target_text.split('\n')
    current_line = 0
    char_count = 0

    for line_idx, line in enumerate(lines):
        output = ""
        for char_idx, char in enumerate(line):
            abs_pos = char_count + char_idx

            # Convert tabs to 4 spaces for display
            display_char = '    ' if char == '\t' else char

            if abs_pos < len(typed_text):
                if typed_text[abs_pos] == char:
                    output += f"{Colors.GREEN}{display_char}{Colors.RESET}"
                else:
                    output += f"{Colors.RED}{display_char}{Colors.RESET}"
            elif abs_pos == current_pos:
                # Highlight current character in tan-orange
                output += f"{Colors.ORANGE}{Colors.BOLD}{display_char}{Colors.RESET}"
            else:
                output += f"{Colors.DIM}{display_char}{Colors.RESET}"

        print(output)
        char_count += len(line)

        # Account for newline character
        if line_idx < len(lines) - 1:
            if char_count < len(typed_text):
                print()  # Typed past this line
            elif char_count == current_pos:
                print(f"{Colors.ORANGE}{Colors.BOLD}↵{Colors.RESET}")  # Highlight newline in orange
            else:
                print()  # Haven't reached this line yet
            char_count += 1

def calculate_metrics(target_text, typed_text, elapsed_time):
    """Calculate typing metrics."""
    total_chars = len(target_text)
    typed_chars = len(typed_text)
    correct_chars = sum(1 for i, c in enumerate(typed_text) if i < len(target_text) and c == target_text[i])
    incorrect_chars = typed_chars - correct_chars

    minutes = elapsed_time / 60
    cpm = correct_chars / minutes if minutes > 0 else 0
    wpm = cpm / 5 if minutes > 0 else 0  # Standard: 5 chars = 1 word
    accuracy = (correct_chars / typed_chars * 100) if typed_chars > 0 else 0

    return {
        'total_chars': total_chars,
        'typed_chars': typed_chars,
        'correct_chars': correct_chars,
        'incorrect_chars': incorrect_chars,
        'cpm': cpm,
        'wpm': wpm,
        'accuracy': accuracy,
        'time': elapsed_time
    }

def display_results(metrics):
    """Display final results."""
    clear_screen()
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}RESULTS{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*80}{Colors.RESET}\n")

    print(f"{Colors.BOLD}Time Elapsed:{Colors.RESET} {timedelta(seconds=int(metrics['time']))}")
    print(f"{Colors.BOLD}Characters Per Minute (CPM):{Colors.RESET} {Colors.GREEN}{metrics['cpm']:.1f}{Colors.RESET}")
    print(f"{Colors.BOLD}Words Per Minute (WPM):{Colors.RESET} {Colors.GREEN}{metrics['wpm']:.1f}{Colors.RESET}")
    print(f"{Colors.BOLD}Accuracy:{Colors.RESET} {Colors.GREEN if metrics['accuracy'] >= 95 else Colors.YELLOW}{metrics['accuracy']:.1f}%{Colors.RESET}")
    print(f"\n{Colors.BOLD}Character Breakdown:{Colors.RESET}")
    print(f"  Total Characters: {metrics['total_chars']}")
    print(f"  {Colors.GREEN}Correct: {metrics['correct_chars']}{Colors.RESET}")
    print(f"  {Colors.RED}Incorrect: {metrics['incorrect_chars']}{Colors.RESET}")
    print(f"\n{Colors.CYAN}{'='*80}{Colors.RESET}\n")

def main():
    try:
        # Load problem
        problem_id, target_text = load_random_problem()

        clear_screen()
        display_header(problem_id)

        # Wait for user to start
        print(f"{Colors.BOLD}Press any key to start...{Colors.RESET}")
        get_char()

        # Initialize
        typed_text = ""
        start_time = time.time()
        current_pos = 0

        clear_screen()
        display_header(problem_id)
        print()

        # Main typing loop
        while current_pos < len(target_text):
            display_header(problem_id)
            print()
            display_text_with_cursor(target_text, typed_text, current_pos)

            char = get_char()

            # Handle special keys
            if ord(char) == 3:  # Ctrl+C
                raise KeyboardInterrupt
            elif ord(char) == 127:  # Backspace
                if typed_text:
                    typed_text = typed_text[:-1]
                    current_pos = max(0, current_pos - 1)
            else:
                typed_text += char
                current_pos += 1

        # Calculate elapsed time
        elapsed_time = time.time() - start_time

        # Calculate and display metrics
        metrics = calculate_metrics(target_text, typed_text, elapsed_time)
        display_results(metrics)

    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Test cancelled.{Colors.RESET}\n")
        sys.exit(0)
    except FileNotFoundError:
        print(f"{Colors.RED}Error: problems.json not found!{Colors.RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"{Colors.RED}Error: {e}{Colors.RESET}")
        sys.exit(1)

if __name__ == "__main__":
    main()