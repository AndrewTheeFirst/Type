from cursestools import Panel
import curses
from random import choice
from threading import Thread
from time import time_ns

def get_prompt():
    with open("prompts.txt") as file:
        lines = file.readlines()
        return choice(lines)
        
class TypeWindow:
    def __init__(self):
        self.typing = False
        self.elapsed_time = 0

        stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        curses.curs_set(0)
        curses.start_color()
        H_SHRINK = 40
        V_SHRINK = 6
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_RED)
        height, width = stdscr.getmaxyx()
        self.height, self.width = height - 2 - V_SHRINK, width - 2 - H_SHRINK
        self.page = Panel(height - V_SHRINK, width - H_SHRINK, V_SHRINK // 2, H_SHRINK // 2, outline=True)
    
    def get_lines(self, prompt: str):
        index = 0
        lines: list[str] = []
        while True:
            string = prompt[index:] # the rest of the string
            if len(string) > self.width: # if the string does not fit in the window
                substring = string[:self.width] # get the part of the string that does fit
                # get the last space index of the substring -- which is the end of the string we will display
                rev_substring = substring[::-1]
                last_space = rev_substring.find(" ")
                end = len(substring) - 1 - last_space
                lines.append(substring[:end + 1])
                index += end + 1
            else:
                lines.append(string)
                break
        return lines

    def print_lines(self, lines):
        for line_num, line in enumerate(lines, 2):
            offset = (self.width - len(line)) // 2
            self.page.addstr(line_num, offset, line)
            self.page.refresh()

    def timer(self):
        start_time = time_ns() * 10**(-9)
        while self.typing:
            current_time = time_ns() * 10**(-9)
            self.elapsed_time = current_time - start_time
            mins = self.elapsed_time // 60
            secs = self.elapsed_time % 60
            if mins:
                time_prompt = f"Elapsed Time: {int(mins)}:{int(secs):02d}"
            else:
                time_prompt = f"Elapsed Time: {secs:.2f}s"
            self.page.addstr(0, (self.width - 2 - len(time_prompt)) // 2, time_prompt)
            self.page.refresh()

    def main_loop(self):
        while True:
            prompt = get_prompt()
            lines = self.get_lines(prompt)
            self.print_lines(lines)
            self.typing = True

            # START TIMER
            t = Thread(target=self.timer)
            t.start()

            # START TYPING
            for line_num, line in enumerate(lines, 2):
                index = (self.width - len(line)) // 2
                for char in line:
                    self.page.chgat(line_num, index, 1, curses.A_STANDOUT)
                    self.page.noutrefresh()
                    while char != chr(self.page.getch()):
                        self.page.chgat(line_num, index, 1, curses.color_pair(1))
                        self.page.noutrefresh()
                    self.page.chgat(line_num, index, 1, curses.A_NORMAL)
                    index += 1
                    
            # STOP TIMER, SHOW WPM
            self.typing = False
            self.page.addstr(0, 0, f"WPM: {round((sum([len(line) for line in lines]) / 5) * (60 / self.elapsed_time))}")
            self.page.refresh()
            self.page.getch()
            self.page.clear()
    
TypeWindow().main_loop()