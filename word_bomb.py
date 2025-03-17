import ctypes
from random import choice
from time import sleep
from pydirectinput import write, press

def get_window_titles(user32) -> list[str]:
    titles = []

    def enum_windows_callback(hwnd, lParam):
        if user32.IsWindowVisible(hwnd):
            buffer = ctypes.create_unicode_buffer(512)  # Get window title
            user32.GetWindowTextW(hwnd, buffer, 512)
            title = buffer.value
            if title:
                titles.append(title)
        return True

    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM) # Define the callback function type
    user32.EnumWindows(EnumWindowsProc(enum_windows_callback), 0) # Enumerate all windows
    return titles

def focus_window(user32, title: str):
    hwnd = user32.FindWindowW(None, title)
    if hwnd:
        user32.SetForegroundWindow(hwnd) # Focus window
    else:
        print(f"Window '{title}' not found!")

def load_words(words_file: str) -> list[str]:
    with open(words_file, "r") as file:
        return [line.strip() for line in file]

def add_word(words_file: str, word: str) -> bool:
    with open(words_file, "r+") as file:
        content = file.read()
        if word in content:
            return False # Word already in list
        file.seek(0, 0)
        file.write(word + "\n" + content)
        return True

def remove_word(words_file: str, word: str) -> bool:
    with open(words_file, "r+") as file:
        lines = file.readlines()
        new_lines = [line for line in lines if line.strip() != word]
        if len(lines) == len(new_lines):
            return False # Word not found
        file.seek(0)
        file.writelines(new_lines)
        file.truncate()
        return True

def select_windows(window_titles: list[str], auto) -> (str):
    cmd_window = ""
    roblox_window = ""
    
    if auto:
        for title in window_titles:
            if title.startswith("Command Prompt") and cmd_window == "": # Only select Command Prompt window if word_bomb.exe isn't found
                cmd_window = title
            elif title.endswith("word_bomb.exe"): 
                cmd_window = title
            elif title.startswith("Roblox"):
                roblox_window = title

    if not cmd_window or not roblox_window:
        for idx, title in enumerate(window_titles):
            print(f"{idx+1}. {title}")
        while True:
            try:
                cmd_window = window_titles[int(input("Select Terminal window: "))-1]
                roblox_window = window_titles[int(input("Select Roblox window: "))-1]
            except (ValueError, IndexError):
                print("Invalid input.")
                continue
            break

    return cmd_window, roblox_window

def find_words(prompt: str, list: list[str], number: int) -> list[str]:
    matches = []
    for word in list:
        if len(matches) >= number:
            break
        if prompt in word:
            matches.append(word)
    return matches

def main():
    user32 = ctypes.windll.user32
    filename = "word_list.txt"
    window_titles = get_window_titles(user32)
    cmd_window, roblox_window = select_windows(window_titles, auto=True)
    word_list = load_words(filename)
    focus_terminal = True
    sample_size = 5
    delay = 20

    print("Enter prompt. /settings for settings.")

    while True:
        cmd = input("> ").split()
        if not cmd:
            continue
        elif cmd[0] == "/s":
            if len(cmd) > 1:
                matches = find_words(cmd[1], reversed(word_list), int(cmd[2]) if len(cmd) > 2 and cmd[2].isdigit() else 3)
                if not matches:
                    print("No matches found.")
                else:
                    for match in matches:
                        print(match)
            else:
                print("Enter a prompt to search.")
        elif cmd[0] == "/reset":
            word_list = load_words(filename)
            print("Reset used words list.")
        elif cmd[0] == "/delay":
            if len(cmd) > 1 and cmd[1].isdigit():
                if (new := int(cmd[1])) > 3000:
                    print("Delay cannot exceed 3000ms.")
                    continue
                print(f"{delay}ms -> {new}ms") 
                delay = int(cmd[1])
            else:
                print(f"{delay}ms")
        elif cmd[0] == "/windows":
            cmd_window, roblox_window = select_windows(window_titles, auto=False)
        elif cmd[0] == "/focus":
            focus_terminal = not focus_terminal
            print(f"Focus terminal window after typing: {not focus_terminal} -> {focus_terminal}")
        elif cmd[0] == "/random":
            if len(cmd) > 1 and cmd[1].isdigit():
                print(f"{sample_size} -> {int(cmd[1])}")
                sample_size = int(cmd[1])
            else:
                print(sample_size)
        elif cmd[0] == "/addword":
            if len(cmd) > 1:
                if add_word(filename, cmd[1]):
                    word_list = [cmd[1]] + word_list
                    print(f"Added '{cmd[1]}' to word list.")
                else:
                    print(f"'{cmd[1]}' already in word list.")
        elif cmd[0] == "/removeword":
            if len(cmd) > 1:
                if remove_word(filename, cmd[1]):
                    if cmd[1] in word_list:
                        word_list.remove(cmd[1])
                    print(f"Removed '{cmd[1]}' from word list.")
                else:
                    print(f"'{cmd[1]}' not found in word list.")
        elif cmd[0] == "/quit":
            break
        elif cmd[0] == "/settings":
            print("/s <prompt> <number> to search a prompt.")
            print("/reset to reset used words list.")
            print("/delay <ms> to change delay between key presses (<10ms not recommended).")
            print("/windows to change selected windows.")
            print("/focus to change whether the terminal window is automatically refocused.")
            print("/random <size> to change sample size for random word selection (how many matches to choose from).")
            print("/addword <word> to add a word to the word list text file.")
            print("/removeword <word> to delete a word from the word list text file.")
            print("/quit to quit.")
        else:
            matches = find_words(cmd[0], word_list, sample_size)
            if not matches:
                print("No matches found. Try /reset.")
                continue
            word = choice(matches)
            focus_window(user32, roblox_window)
            write(word, delay/1000)
            sleep(0.1) # Sleep necessary to avoid jank
            press("enter") # Extra enter press sometimes necessary
            sleep(0.1)
            word_list.remove(word)
            print(word)
            if focus_terminal:
                focus_window(user32, cmd_window)

if __name__ == "__main__":
    main()
