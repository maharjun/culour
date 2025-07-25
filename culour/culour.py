import os
import curses

COLOR_PAIRS_CACHE = {}


class TerminalColors(object):
    WHITE = '[97'
    CYAN = '[96'
    MAGENTA = '[95'
    BLUE = '[94'
    YELLOW = '[93'
    GREEN = '[92'
    RED = '[91'
    BLACK = '[90'
    END = '[0'
    # Style codes
    BOLD = '[1'
    UNDERLINE = '[4'


# Translates between the terminal notation of a color, to it's curses color number
TERMINAL_COLOR_TO_CURSES = {
    TerminalColors.BLACK: curses.COLOR_BLACK,
    TerminalColors.RED: curses.COLOR_RED,
    TerminalColors.GREEN: curses.COLOR_GREEN,
    TerminalColors.YELLOW: curses.COLOR_YELLOW,
    TerminalColors.BLUE: curses.COLOR_BLUE,
    TerminalColors.MAGENTA: curses.COLOR_MAGENTA,
    TerminalColors.CYAN: curses.COLOR_CYAN,
    TerminalColors.WHITE: curses.COLOR_WHITE
}


def _get_color(fg, bg):
    key = (fg, bg)
    if key not in COLOR_PAIRS_CACHE:
        # Use the pairs from 101 and after, so there's less chance they'll be overwritten by the user
        pair_num = len(COLOR_PAIRS_CACHE) + 1
        curses.init_pair(pair_num, fg, bg)
        COLOR_PAIRS_CACHE[key] = pair_num

    return COLOR_PAIRS_CACHE[key]


def _parse_ansi_code(code_str):
    """Parse ANSI code string and return (color_pair, attributes)"""
    fg = curses.COLOR_WHITE
    attributes = 0
    
    # Handle style codes
    if code_str == TerminalColors.BOLD:
        attributes |= curses.A_BOLD
    elif code_str == TerminalColors.UNDERLINE:
        attributes |= curses.A_UNDERLINE
    elif code_str == TerminalColors.END:
        # Reset to defaults
        fg = curses.COLOR_WHITE
        attributes = 0
    elif code_str in TERMINAL_COLOR_TO_CURSES:
        # Handle color codes
        fg = TERMINAL_COLOR_TO_CURSES[code_str]
    
    color_pair = _get_color(fg, curses.COLOR_BLACK)
    return color_pair, attributes


def _add_line(y, x, window, line):
    # split but \033 which stands for a color change
    color_split = line.split('\033')

    # Print the first part of the line without color change
    default_color_pair = _get_color(curses.COLOR_WHITE, curses.COLOR_BLACK)
    window.addstr(y, x, color_split[0], curses.color_pair(default_color_pair))
    x += len(color_split[0])

    # Track current attributes across the line
    current_attributes = 0
    current_color_pair = default_color_pair

    # Iterate over the rest of the line-parts and print them with their colors
    for substring in color_split[1:]:
        code_str = substring.split('m')[0]
        substring = substring[len(code_str)+1:]
        
        # Parse the ANSI code
        color_pair, attributes = _parse_ansi_code(code_str)
        
        # Update current state
        if code_str == TerminalColors.END:
            # Reset everything
            current_attributes = 0
            current_color_pair = default_color_pair
        elif code_str in [TerminalColors.BOLD, TerminalColors.UNDERLINE]:
            # Add to existing attributes
            current_attributes |= attributes
        else:
            # Color change - keep existing attributes
            current_color_pair = color_pair
        
        # Apply both color and attributes
        display_attrs = curses.color_pair(current_color_pair) | current_attributes
        window.addstr(y, x, substring, display_attrs)
        x += len(substring)


def _inner_addstr(window, string, y=-1, x=-1):
    assert curses.has_colors(), "Curses wasn't configured to support colors. Call curses.start_color()"

    cur_y, cur_x = window.getyx()
    if y == -1:
        y = cur_y
    if x == -1:
        x = cur_x
    for line in string.split(os.linesep):
        _add_line(y, x, window, line)
        # next line
        y += 1


def addstr(*args):
    """
    Adds the color-formatted string to the given window, in the given coordinates
    To add in the current location, call like this:
        addstr(window, string)
    and to set the location to print the string, call with:
        addstr(window, y, x, string)
    Only use color pairs up to 100 when using this function,
    otherwise you will overwrite the pairs used by this function
    """
    if len(args) != 2 and len(args) != 4:
        raise TypeError("addstr requires 2 or 4 arguments")

    if len(args) == 4:
        window = args[0]
        y = args[1]
        x = args[2]
        string = args[3]
    else:
        window = args[0]
        string = args[1]
        y = -1
        x = -1

    return _inner_addstr(window, string, y, x)
