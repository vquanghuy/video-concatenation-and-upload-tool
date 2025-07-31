import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext
import subprocess
import os
from datetime import datetime
import threading
import queue

# Global variable to store the last selected path
ffmpeg_output_queue = queue.Queue()
last_selected_path = "last_path.txt"

def center_window(root, width=500, height=300):
    # Get the screen dimensions
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    # Calculate x and y coordinates for the Tk window
    x = (screen_width/2) - (width/2)
    y = (screen_height/2) - (height/2)

    root.geometry('%dx%d+%d+%d' % (width, height, x, y))


def save_last_selected_path(path):
    with open(last_selected_path, 'w') as file:
        file.write(path)


def load_last_selected_path():
    try:
        with open(last_selected_path, 'r') as file:
            return file.read().strip()
    except FileNotFoundError:
        return ""

def select_folder():
    folder = filedialog.askdirectory(initialdir=load_last_selected_path())
    if folder:
        input_entry.delete(0, tk.END)
        input_entry.insert(0, folder)
        set_output_filename(folder)
        save_last_selected_path(folder)


def set_output_filename(folder):
    current_time = datetime.now().strftime("%b-%d-%Y-%H-%M")
    output_filename = f"{current_time}.mp4"
    output_entry.delete(0, tk.END)
    output_entry.insert(0, output_filename)

def update_console_text():
    global console_text
    while not ffmpeg_output_queue.empty():
        line = ffmpeg_output_queue.get()
        if line is not None:
            console_text.insert(tk.END, line)
            console_text.see(tk.END)
        else:  # We got the signal that the process is done
            break

    app.after(100, update_console_text)  # Check the queue again after 100 ms


def ffmpeg_thread(ffmpeg_command):
    process = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)

    for line in iter(process.stdout.readline, ''):
        ffmpeg_output_queue.put(line)

    process.stdout.close()
    process.wait()

    ffmpeg_output_queue.put("\n--------------\n")
    ffmpeg_output_queue.put("-----DONE-----\n")
    ffmpeg_output_queue.put("--------------\n")
    ffmpeg_output_queue.put(None)  # Signal that the process is done

def open_output_directory():
    folder = filedialog.askdirectory()
    if folder:
        output_entry.delete(0, tk.END)
        output_entry.insert(0, folder)


def concatenate_videos():
    input_folder = input_entry.get().strip()
    output_file = output_entry.get().strip()
    output_path = os.path.join(input_folder, '..', output_file)

    if not input_folder or not output_file:
        messagebox.showwarning("Warning", "Please select a source folder and set an output file name.")
        return

    # Generate the input.txt file
    input_txt_path = os.path.join(input_folder, 'input.txt')
    with open(input_txt_path, 'w') as file:
        for filename in sorted(os.listdir(input_folder)):
            if filename.endswith(('.mp4', '.MP4', '.MOV')):
                file_path = os.path.join(input_folder, filename)
                # Wrap file paths with spaces in single quotes
                file.write(f"file '{file_path}'\n")

    # Run FFmpeg command
    ffmpeg_command = ['ffmpeg', '-f', 'concat', '-safe', '0', '-i', input_txt_path, '-c', 'copy', output_path]

    # Clear the console_text widget
    console_text.configure(state='normal')
    console_text.delete('1.0', tk.END)  # Clears the text from start ('1.0') to end

    console_text.insert(tk.END, "\n-------------\n")
    console_text.insert(tk.END, "FFMPEG command:\n")
    console_text.insert(tk.END, " ".join(ffmpeg_command))
    console_text.insert(tk.END, "\n-------------\n")
    threading.Thread(target=ffmpeg_thread, args=(ffmpeg_command,), daemon=True).start()

def initialize_ui(root):
    root.title('Video Concatenation and Upload Tool')

    ttk.Label(root, text="Input").grid(row=0, column=0, padx=10, pady=10)
    global input_entry
    input_entry = ttk.Entry(root)
    input_entry.grid(row=0, column=1, padx=10, pady=10)
    ttk.Button(root, text="Select", command=select_folder).grid(row=0, column=2, padx=10, pady=10)

    ttk.Label(root, text="Output").grid(row=1, column=0, padx=10, pady=10)
    global output_entry
    output_entry = ttk.Entry(root)
    output_entry.grid(row=1, column=1, padx=10, pady=10)
    ttk.Button(root, text="Open", command=open_output_directory).grid(row=1, column=2, padx=10, pady=10)

    global console_text
    console_text = scrolledtext.ScrolledText(app, height=10)
    console_text.grid(row=2, column=0, columnspan=3, padx=10, pady=10)

    start_button = ttk.Button(root, text="Start", command=concatenate_videos)
    start_button.grid(row=3, column=1, padx=10, pady=10, sticky='ew')

    # load last path automatically
    last_path = load_last_selected_path()
    if last_path:
        input_entry.insert(0, last_path)
        set_output_filename(last_path)  # Set the output filename based on the last path

# Main application code
app = tk.Tk()

center_window(app, 600, 300)
initialize_ui(app)
app.after(100, update_console_text)

app.mainloop()
