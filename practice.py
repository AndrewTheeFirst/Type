from cursestools import Panel
import curses
from random import choice
from threading import Thread
from time import time_ns
from typing import Literal

def get_difficulty(prompt: int) -> Literal["story", "hard", "medium", "easy"]:
    prompt_length = len(prompt)
    if prompt_length > 750:
        return "story"
    elif prompt_length > 350:
        return "hard"
    elif prompt_length > 175:
        return "medium"
    else:
        return "easy"
        
class TypeWindow:
    def __init__(self, difficulty: Literal["story", "hard", "medium", "easy"] = ""):
        self.typing = False
        self.elapsed_time = 0
        self.difficulty = difficulty

        stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        curses.curs_set(0)
        curses.start_color()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_RED)
        curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_GREEN)
        H_PADDING = 40
        V_PADDING = 6
        height, width = stdscr.getmaxyx()
        self.width = width - H_PADDING - 2 # -2 accounts for border
        self.typing_window = Panel(height - V_PADDING, width - H_PADDING, V_PADDING // 2, H_PADDING // 2, outline=True)
    
    def get_lines(self, prompt: str) -> list[str]:
        index = 0
        lines = []
        while True:
            string = prompt[index:] # the rest of the string
            if len(string) > self.width: # if the string does not fit in the window
                fitting_string = string[:self.width] # get the part of the string that does fit
                # get the last space index of the substring -- which is the end of the string we will display
                rev_substring = fitting_string[::-1]
                rev_first_space = rev_substring.find(" ")
                subs_last_space = len(fitting_string) - 1 - rev_first_space
                lines.append(fitting_string[:subs_last_space + 1]) # include that space in the line
                index += subs_last_space + 1 # start after where we stopped
            else:
                lines.append(string)
                return lines

    def print_lines(self, lines: list[str]) -> None: 
        for line_num, line in enumerate(lines, 2):
            offset = (self.width - len(line)) // 2 # center text
            self.typing_window.addstr(line_num, offset, line)
            self.typing_window.refresh()

    def timer(self) -> None:
        start_time = time_ns() * 10**(-9)
        while self.typing:
            current_time = time_ns() * 10**(-9)
            self.elapsed_time = current_time - start_time
            mins = self.elapsed_time // 60
            secs = self.elapsed_time % 60
            time_prompt = "  Elapsed Time: " + (f"{int(mins)}:{int(secs):02d}" if mins else f"{secs:.2f}s  ")
            self.typing_window.addstr(0, (self.width - len(time_prompt)) // 2, time_prompt)
            self.typing_window.addstr(0, 0, f"WPM: {round(self.num_chars_typed / 5 * (60 / self.elapsed_time))}")
            self.typing_window.refresh()
        self.typing_window.addstr(0, 0, f"FINAL WPM: {round(self.num_chars_typed / 5 * (60 / self.elapsed_time))}")
        self.typing_window.refresh()
    
    def get_prompt(self) -> str:
        with open("prompts.txt") as file:
            lines = file.readlines()
            prompt = choice(lines).rstrip()
            if self.difficulty:
                while get_difficulty(prompt) != self.difficulty:
                    prompt = choice(lines).rstrip()
            return prompt
            
    def main_loop(self) -> None:
        while True:
            self.num_chars_typed = 0

            # SELECT / INSERT PROMPT
            prompt = self.get_prompt()
            difficulty = get_difficulty(prompt)
            lines = self.get_lines(prompt)
            self.print_lines(lines)
            self.typing_window.addstr(0, self.width - len(difficulty) - 1, difficulty)
            self.typing = True

            # START TIMER
            t = Thread(target=self.timer)
            t.start()

            # START TYPING
            for line_num, line in enumerate(lines, 2):
                index = (self.width - len(line)) // 2
                for char in line:
                    self.typing_window.chgat(line_num, index, 1, curses.A_STANDOUT)
                    self.typing_window.noutrefresh()
                    while char != chr(self.typing_window.getch()):
                        self.typing_window.chgat(line_num, index, 1, curses.color_pair(1)) # 
                        self.typing_window.noutrefresh()
                    self.num_chars_typed += 1
                    self.typing_window.chgat(line_num, index, 1, curses.A_NORMAL)
                    self.typing_window.chgat(line_num, index, 1, curses.color_pair(2))
                    index += 1
                    
            # STOP TIMER, SHOW FINAL WPM
            self.typing = False
            self.typing_window.getch()
            self.typing_window.clear()

if __name__ == "__main__":
    prog = TypeWindow("") # leave blank for random difficulty
    prog.main_loop()