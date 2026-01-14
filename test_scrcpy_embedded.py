"""
Embedded Scrcpy Test - RT1018 Installer
Tests embedding scrcpy window inside tkinter frame
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import subprocess
import time
import sys

# Try to import Windows-specific modules
try:
    import win32gui
    import win32con
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False
    print("WARNING: pywin32 not installed. Install with: pip install pywin32")


class EmbeddedScrcpyTester:
    def __init__(self, root):
        self.root = root
        self.root.title("Embedded Scrcpy Test - RT1018")
        self.root.geometry("1000x700")

        self.scrcpy_process = None
        self.scrcpy_hwnd = None
        self.embed_frame = None

        self.setup_ui()

        if not HAS_WIN32:
            self.log("ERROR: pywin32 not installed!", "ERROR")
            self.log("Install with: pip install pywin32", "INFO")

    def setup_ui(self):
        """Setup the test UI"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title = ttk.Label(main_frame, text="Embedded Scrcpy Test",
                         font=("Arial", 14, "bold"))
        title.pack(pady=(0, 10))

        # Device selection
        device_frame = ttk.LabelFrame(main_frame, text="Device", padding="5")
        device_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(device_frame, text="Device IP:Port:").pack(side=tk.LEFT, padx=5)
        self.device_var = tk.StringVar(value="192.168.0.7:1206")
        ttk.Entry(device_frame, textvariable=self.device_var, width=20).pack(side=tk.LEFT, padx=5)

        self.start_btn = ttk.Button(device_frame, text="Start Embedded Scrcpy",
                                    command=self.start_embedded_scrcpy)
        self.start_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = ttk.Button(device_frame, text="Stop",
                                   command=self.stop_scrcpy, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        # Scrcpy embed frame (960x540)
        scrcpy_container = ttk.LabelFrame(main_frame, text="Scrcpy Screen (960×540)", padding="5")
        scrcpy_container.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.embed_frame = tk.Frame(scrcpy_container, width=960, height=540,
                                    bg='black', relief=tk.SUNKEN, bd=2)
        self.embed_frame.pack(fill=tk.BOTH, expand=True)
        self.embed_frame.pack_propagate(False)

        # Placeholder label
        self.placeholder = tk.Label(self.embed_frame,
                                   text="Scrcpy will appear here\n\n(960×540)",
                                   bg='black', fg='white',
                                   font=('Arial', 16))
        self.placeholder.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        # Log
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="5")
        log_frame.pack(fill=tk.X)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def log(self, message, level="INFO"):
        """Add log message"""
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{level}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)
        print(f"[{level}] {message}")

    def start_embedded_scrcpy(self):
        """Start scrcpy and embed it in the frame"""
        if not HAS_WIN32:
            self.log("Cannot embed: pywin32 not installed", "ERROR")
            return

        device = self.device_var.get().strip()
        if not device:
            self.log("Please enter device IP:Port", "ERROR")
            return

        if self.scrcpy_process:
            self.log("Scrcpy already running", "WARNING")
            return

        self.log(f"Starting scrcpy for {device}...")
        self.placeholder.config(text="Starting scrcpy...\nPlease wait...")

        try:
            # Start scrcpy with no window decorations and specific title
            # We need a unique title to find the window
            window_title = f"RT1018_EMBED_{int(time.time())}"

            cmd = [
                "scrcpy",
                "-s", device,
                "--window-title", window_title,
                "--window-borderless",
                "--always-on-top",
                "--window-width", "960",
                "--window-height", "540"
            ]

            self.log(f"Command: {' '.join(cmd)}")

            # Start scrcpy
            self.scrcpy_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            self.log(f"Scrcpy started (PID: {self.scrcpy_process.pid})")
            self.log("Waiting for scrcpy window to appear...")

            # Wait for window to appear and embed it
            self.root.after(2000, lambda: self.find_and_embed_window(window_title))

            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)

        except Exception as e:
            self.log(f"Failed to start: {str(e)}", "ERROR")
            self.placeholder.config(text="Failed to start scrcpy")

    def find_and_embed_window(self, window_title):
        """Find scrcpy window and embed it"""
        if not HAS_WIN32:
            return

        self.log(f"Looking for window: {window_title}")

        # Find the scrcpy window
        hwnd = win32gui.FindWindow(None, window_title)

        if hwnd:
            self.log(f"Found window! HWND: {hwnd}")
            self.scrcpy_hwnd = hwnd

            # Get the frame's window handle
            frame_hwnd = self.embed_frame.winfo_id()
            self.log(f"Frame HWND: {frame_hwnd}")

            try:
                # Remove window decorations
                style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
                style &= ~(win32con.WS_CAPTION | win32con.WS_THICKFRAME | win32con.WS_MINIMIZE | win32con.WS_MAXIMIZE | win32con.WS_SYSMENU)
                win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, style)

                # Set parent to our frame
                win32gui.SetParent(hwnd, frame_hwnd)

                # Resize and position
                self.log("Resizing and positioning window...")
                win32gui.SetWindowPos(
                    hwnd,
                    win32con.HWND_TOP,
                    0, 0,  # Position
                    960, 540,  # Size
                    win32con.SWP_SHOWWINDOW
                )

                self.log("✓ Scrcpy embedded successfully!", "SUCCESS")
                self.placeholder.pack_forget()  # Hide placeholder

                # Monitor the window
                self.root.after(1000, self.monitor_embedded_window)

            except Exception as e:
                self.log(f"Failed to embed: {str(e)}", "ERROR")
                self.placeholder.config(text=f"Embedding failed:\n{str(e)}")

        else:
            self.log("Window not found yet, retrying...", "WARNING")
            # Try again
            if self.scrcpy_process and self.scrcpy_process.poll() is None:
                self.root.after(1000, lambda: self.find_and_embed_window(window_title))
            else:
                self.log("Scrcpy process died", "ERROR")
                self.placeholder.config(text="Scrcpy failed to start")
                self.start_btn.config(state=tk.NORMAL)
                self.stop_btn.config(state=tk.DISABLED)

    def monitor_embedded_window(self):
        """Monitor the embedded window and process"""
        if self.scrcpy_process:
            poll = self.scrcpy_process.poll()
            if poll is None:
                # Still running
                # Make sure window is still properly positioned
                if self.scrcpy_hwnd and HAS_WIN32:
                    try:
                        win32gui.SetWindowPos(
                            self.scrcpy_hwnd,
                            win32con.HWND_TOP,
                            0, 0,
                            960, 540,
                            win32con.SWP_SHOWWINDOW
                        )
                    except:
                        pass

                self.root.after(1000, self.monitor_embedded_window)
            else:
                # Process ended
                self.log(f"Scrcpy stopped (exit code: {poll})", "INFO")
                self.cleanup_scrcpy()

    def stop_scrcpy(self):
        """Stop scrcpy"""
        if self.scrcpy_process:
            self.log("Stopping scrcpy...")
            try:
                self.scrcpy_process.terminate()
                self.scrcpy_process.wait(timeout=5)
            except:
                self.scrcpy_process.kill()

            self.cleanup_scrcpy()

    def cleanup_scrcpy(self):
        """Cleanup after scrcpy stops"""
        self.scrcpy_process = None
        self.scrcpy_hwnd = None

        self.placeholder.pack(fill=tk.BOTH, expand=True)
        self.placeholder.config(text="Scrcpy will appear here\n\n(960×540)")

        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.log("Scrcpy stopped")

    def on_closing(self):
        """Handle window close"""
        self.stop_scrcpy()
        self.root.destroy()


def main():
    if not HAS_WIN32:
        print("\n" + "="*60)
        print("ERROR: pywin32 not installed!")
        print("="*60)
        print("\nTo embed scrcpy, you need pywin32:")
        print("  pip install pywin32")
        print("\nPress Enter to continue anyway (won't be able to embed)...")
        print("="*60 + "\n")
        input()

    root = tk.Tk()
    app = EmbeddedScrcpyTester(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    print("="*60)
    print("Embedded Scrcpy Test - RT1018 Installer")
    print("="*60)
    print("\nThis tests embedding scrcpy inside tkinter window")
    print("Requires: pywin32 (pip install pywin32)")
    print("="*60 + "\n")

    main()
