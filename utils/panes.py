import curses
from threading import Thread
import queue

# Dictionary to store pane information
panes = {}
input_queue = queue.Queue()
running = True  # Control flag for the main loop
selected_pane = "bottom_left"  # Default selected pane

# Function to initialize color pairs
def init_colors():
    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)

# Function to wrap text to fit within a given width
def wrap_text(text, width):
    lines = []
    for paragraph in text.split('\n'):
        line = ""
        for word in paragraph.split():
            if len(line) + len(word) + 1 > width:
                lines.append(line)
                line = word
            else:
                if line:
                    line += " " + word
                else:
                    line = word
        lines.append(line)
    return lines

# Function to update a pane with multiline text or a list of objects
def update_pane(pane_name, new_text=None, streamed=False):
    global panes
    pane = panes[pane_name]
    pane_width = curses.COLS // 2 - 2  # Calculate the pane width, considering borders
    pane_height = pane["height"] - 2  # Available height considering borders

    if new_text is not None:
        if isinstance(new_text, str):
            new_lines = wrap_text(new_text, pane_width)
        elif isinstance(new_text, list):
            new_lines = []
            for obj in new_text:
                new_lines.extend(wrap_text(f"{obj['role']}: {obj['content']}", pane_width))

        if streamed and new_lines:
            # Concatenate new text to the existing last line with a space separator until the width is reached
            for line in new_lines:
                while len(line) > 0:
                    if len(pane["buffer"]) == 0 or len(pane["buffer"][-1]) >= pane_width:
                        pane["buffer"].append("")
                    space_left = pane_width - len(pane["buffer"][-1])
                    if len(pane["buffer"][-1]) > 0:
                        pane["buffer"][-1] += " "
                        space_left -= 1
                    pane["buffer"][-1] += line[:space_left]
                    line = line[space_left:]
                    if len(pane["buffer"]) > 1000:
                        pane["buffer"].pop(0)
        else:
            for line in new_lines:
                while len(line) > pane_width:
                    pane["buffer"].append(line[:pane_width])
                    line = line[pane_width:]
                    if len(pane["buffer"]) > 1000:
                        pane["buffer"].pop(0)
                pane["buffer"].append(line)
                if len(pane["buffer"]) > 1000:
                    pane["buffer"].pop(0)

    # Always scroll to the bottom of the buffer unless specified otherwise
    if new_text is not None:
        pane["scroll_position"] = max(0, len(pane["buffer"]) - pane_height)
    pane["visible_lines"] = pane["buffer"][pane["scroll_position"]:pane["scroll_position"] + pane_height]
    render_pane(pane_name)

def render_pane(pane_name):
    pane = panes[pane_name]
    pane["win"].clear()
    if pane_name == selected_pane:
        pane["win"].attron(curses.color_pair(1))
        pane["win"].box()
        pane["win"].attroff(curses.color_pair(1))
    else:
        pane["win"].box()
    pane["win"].addstr(0, 2, f" {pane['title']} ", curses.A_BOLD)
    pane_width = curses.COLS // 2 - 2  # Calculate the pane width, considering borders
    for idx, line in enumerate(pane["visible_lines"]):
        try:
            pane["win"].addstr(idx + 1, 1, line[:pane_width])
        except curses.error:
            pass  # Ignore the error if the text can't be added
    pane["win"].refresh()

# Functions to print to each specific pane with multiline support
def print_instructions(text):
    update_pane("top_left", text)

def print_system(text):
    update_pane("top_right", text)

def print_user(text):
    update_pane("bottom_left", text)

def print_llm(text, streamed=False):
    update_pane("bottom_right", text, streamed)

# Function to initialize panes
def draw_panes(stdscr):
    global panes, running, selected_pane
    stdscr.clear()
    init_colors()

    height, width = stdscr.getmaxyx()
    pane_height = height // 2
    pane_width = width // 2

    # Create panes
    panes = {
        "top_left": {"win": stdscr.subwin(pane_height, pane_width, 0, 0), "buffer": [], "visible_lines": [], "scroll_position": 0, "height": pane_height, "title": "Instructions"},
        "top_right": {"win": stdscr.subwin(pane_height, pane_width, 0, pane_width), "buffer": [], "visible_lines": [], "scroll_position": 0, "height": pane_height, "title": "System"},
        "bottom_left": {"win": stdscr.subwin(pane_height, pane_width, pane_height, 0), "buffer": [], "visible_lines": [], "scroll_position": 0, "height": pane_height, "title": "User"},
        "bottom_right": {"win": stdscr.subwin(pane_height, pane_width, pane_height, pane_width), "buffer": [], "visible_lines": [], "scroll_position": 0, "height": pane_height, "title": "LLM Response"}
    }

    # Initial titles
    for name in panes:
        update_pane(name, "")

    input_str = ""
    stdscr.nodelay(False)  # Set getch to blocking mode

    while running:
        for name in panes:
            render_pane(name)

        panes["bottom_left"]["win"].clear()
        panes["bottom_left"]["win"].box()
        panes["bottom_left"]["win"].addstr(0, 2, " User Input ", curses.A_BOLD)
        pane_width = curses.COLS // 2 - 2  # Calculate the pane width, considering borders
        for idx, line in enumerate(panes["bottom_left"]["buffer"][-pane_height:]):
            panes["bottom_left"]["win"].addstr(idx + 1, 1, line[:pane_width])
        panes["bottom_left"]["win"].addstr(len(panes["bottom_left"]["buffer"]) + 1, 1, "Enter text: " + input_str[:pane_width])
        panes["bottom_left"]["win"].refresh()

        char = stdscr.getch()

        if char == curses.KEY_UP:
            pane = panes[selected_pane]
            pane["scroll_position"] = max(0, pane["scroll_position"] - pane["height"])
            update_pane(selected_pane)
        elif char == curses.KEY_DOWN:
            pane = panes[selected_pane]
            pane["scroll_position"] = min(len(pane["buffer"]) - pane["height"], pane["scroll_position"] + pane["height"])
            update_pane(selected_pane)
        elif char == 9:  # Tab key
            pane_names = list(panes.keys())
            selected_index = pane_names.index(selected_pane)
            selected_pane = pane_names[(selected_index + 1) % len(pane_names)]
        elif char in (10, 13):  # Enter key
            if input_str.lower() in ['exit', 'quit']:
                running = False
                break
            wrapped_input = wrap_text(input_str, pane_width)
            for line in wrapped_input:
                panes["bottom_left"]["buffer"].append("Prompt > " + line)
                if len(panes["bottom_left"]["buffer"]) >= 1000:
                    panes["bottom_left"]["buffer"].pop(0)
            input_queue.put(input_str)
            print_user(input_str)
            input_str = ""
        elif char == 27:  # Escape key
            running = False
            break
        elif char == 127:  # Backspace key
            input_str = input_str[:-1]
        elif 0 <= char <= 255:
            input_str += chr(char)

def run_curses_app():
    curses.wrapper(draw_panes)

def start_pane_printer():
    thread = Thread(target=run_curses_app)
    thread.daemon = True
    thread.start()

def get_user_input():
    return input_queue.get()  # Block until an item is available

def stop_pane_printer():
    global running
    running = False

