"""
RT1018 Android Device Installer - GUI Application
Replaces the batch file installer with a full-featured GUI
"""

import json
import os
import shutil
import socket
import sqlite3
import subprocess
import sys
import threading
import time
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import ttk, scrolledtext, messagebox, filedialog

# Windows API for embedding scrcpy
try:
    import win32gui
    import win32con
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False
    print("WARNING: pywin32 not installed. Scrcpy embedding will not work.")
    print("Install with: pip install pywin32")

# Hide console windows on Windows for subprocess calls
SUBPROCESS_FLAGS = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0


class AndroidDevice:
    """Represents an Android device detected on the network"""
    def __init__(self, ip, port=5555):
        self.ip = ip
        self.port = port
        self.version = None
        self.model = None
        self.status = "Disconnected"
        self.selected = False

    def __str__(self):
        return f"{self.ip}:{self.port} - Android {self.version or 'Unknown'} ({self.model or 'Unknown'})"


class RT1018InstallerGUI:
    """Main GUI application for RT1018 Android device installer"""

    def __init__(self, root):
        self.root = root
        self.root.title("RT1018 안드로이드 디바이스 설치 프로그램")
        self.root.geometry("1600x900")  # Wide enough for device list + 960×540 scrcpy frame + padding

        # Application paths
        # Handle both running as script and as PyInstaller executable
        if getattr(sys, 'frozen', False):
            # Running as compiled executable - use executable's directory
            self.base_dir = Path(sys.executable).parent
        else:
            # Running as Python script - use script's directory
            self.base_dir = Path(__file__).parent

        self.files_dir = self.base_dir / "install_files"
        self.backup_dir = self.base_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)

        # Local ADB and Scrcpy paths (bundled with application)
        self.adb_dir = self.base_dir / "adb"
        self.adb_path = self.adb_dir / "adb.exe"
        self.scrcpy_path = self.adb_dir / "scrcpy.exe"

        # Application state
        self.devices = []
        self.device_vars = []
        self.scanning = False
        self.installing = False
        self.scrcpy_process = None
        self.scrcpy_hwnd = None
        self.scrcpy_embed_frame = None
        self.scrcpy_monitor_id = None  # Track monitor callback
        self.scrcpy_search_id = None   # Track window search callback
        self.scrcpy_user_stopped = False  # Track if user intentionally stopped scrcpy
        self.scrcpy_current_device = None  # Track current device for auto-reconnect
        self.scrcpy_retry_count = 0  # Track retry attempts
        self.scrcpy_max_retries = 10  # Maximum retry attempts

        # APK and file paths
        self.app_package = "com.releasetech.eightpresso.basic"
        self.apk_files = [
            "rustdesk-1.1.9.apk",
            "hangulkeyboard.apk",
            "EasyCard-A_v1.0.3.0_mod.apk",
            "EightPresso.apk"
        ]

        self.setup_ui()
        self.check_adb_availability()

        # Auto-detect IP range after UI is set up
        self.auto_detect_ip_range()

    def setup_ui(self):
        """Setup the main UI components"""
        # Create main container
        main_container = ttk.Frame(self.root, padding="10")
        main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_container.columnconfigure(1, weight=1)
        main_container.rowconfigure(2, weight=1)

        # Left panel - Device list
        self.setup_device_panel(main_container)

        # Right panel - Scrcpy screen and controls
        self.setup_control_panel(main_container)

        # Bottom panel - Log and progress
        self.setup_log_panel(main_container)

    def setup_device_panel(self, parent):
        """Setup the left panel with device list"""
        device_frame = ttk.LabelFrame(parent, text="안드로이드 디바이스", padding="10")
        device_frame.grid(row=0, column=0, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))

        # Scan controls
        scan_frame = ttk.Frame(device_frame)
        scan_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(scan_frame, text="IP 범위:").pack(side=tk.LEFT)
        self.ip_range_var = tk.StringVar(value="192.168.1")
        ttk.Entry(scan_frame, textvariable=self.ip_range_var, width=15).pack(side=tk.LEFT, padx=5)

        # Auto-detect button
        self.detect_btn = ttk.Button(scan_frame, text="자동", command=self.auto_detect_ip_range, width=6)
        self.detect_btn.pack(side=tk.LEFT, padx=2)

        self.scan_btn = ttk.Button(scan_frame, text="네트워크 스캔", command=self.scan_network)
        self.scan_btn.pack(side=tk.LEFT, padx=5)

        self.scan_progress = ttk.Progressbar(scan_frame, mode='indeterminate', length=100)
        self.scan_progress.pack(side=tk.LEFT, padx=5)

        # Device list with scrollbar
        list_frame = ttk.Frame(device_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.device_list_canvas = tk.Canvas(list_frame, yscrollcommand=scrollbar.set, bg='white')
        self.device_list_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.device_list_canvas.yview)

        self.device_list_frame = ttk.Frame(self.device_list_canvas)
        self.canvas_window = self.device_list_canvas.create_window(
            (0, 0),
            window=self.device_list_frame,
            anchor=tk.NW,
            tags="device_frame"
        )

        # Update canvas window width when canvas is resized
        def on_canvas_configure(event):
            # Make the frame width match the canvas width
            self.device_list_canvas.itemconfig(self.canvas_window, width=event.width)
            print(f"[DEBUG] Canvas resized to width: {event.width}")

        self.device_list_canvas.bind("<Configure>", on_canvas_configure)

        # Update scroll region when frame size changes
        self.device_list_frame.bind("<Configure>", lambda e: self.device_list_canvas.configure(
            scrollregion=self.device_list_canvas.bbox("all")))

    def setup_control_panel(self, parent):
        """Setup the right panel with scrcpy and controls"""
        control_frame = ttk.Frame(parent)
        control_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Scrcpy screen (embedded, 960x540)
        scrcpy_frame = ttk.LabelFrame(control_frame, text="디바이스 화면 (Scrcpy 960×540)", padding="5")
        scrcpy_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Create embed frame with fixed size
        self.scrcpy_embed_frame = tk.Frame(scrcpy_frame, width=960, height=540,
                                          bg='black', relief=tk.SUNKEN, bd=2)
        self.scrcpy_embed_frame.pack(fill=tk.BOTH, expand=True)
        self.scrcpy_embed_frame.pack_propagate(False)

        # Placeholder label
        self.scrcpy_placeholder = tk.Label(self.scrcpy_embed_frame,
                                          text="디바이스를 선택하고 'Scrcpy 시작'을 클릭하세요\n디바이스 화면이 여기에 표시됩니다\n\n(960×540)",
                                          bg='black', fg='white',
                                          font=('Arial', 12))
        self.scrcpy_placeholder.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        # Control buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X)

        # Installation source selection
        source_frame = ttk.LabelFrame(button_frame, text="설치 소스", padding="5")
        source_frame.pack(fill=tk.X, pady=(0, 10))

        self.install_source_var = tk.StringVar(value="default")
        ttk.Radiobutton(source_frame, text="기본 설정", variable=self.install_source_var,
                       value="default").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(source_frame, text="백업 설정", variable=self.install_source_var,
                       value="backup").pack(side=tk.LEFT, padx=5)

        self.backup_combo = ttk.Combobox(source_frame, state="readonly", width=30)
        self.backup_combo.pack(side=tk.LEFT, padx=5)
        self.refresh_backup_list()

        # Action buttons
        action_frame = ttk.Frame(button_frame)
        action_frame.pack(fill=tk.X, pady=5)

        self.install_btn = ttk.Button(action_frame, text="선택한 디바이스에 설치",
                                     command=self.start_installation, state=tk.DISABLED)
        self.install_btn.pack(side=tk.LEFT, padx=5)

        self.backup_btn = ttk.Button(action_frame, text="디바이스에서 백업",
                                    command=self.start_backup, state=tk.DISABLED)
        self.backup_btn.pack(side=tk.LEFT, padx=5)

        self.cleanup_btn = ttk.Button(action_frame, text="데이터베이스 이미지 정리",
                                     command=self.cleanup_database_images)
        self.cleanup_btn.pack(side=tk.LEFT, padx=5)

        self.scrcpy_btn = ttk.Button(action_frame, text="Scrcpy 시작",
                                     command=self.toggle_scrcpy, state=tk.DISABLED)
        self.scrcpy_btn.pack(side=tk.LEFT, padx=5)

    def setup_log_panel(self, parent):
        """Setup the bottom panel with logs and progress"""
        log_frame = ttk.LabelFrame(parent, text="설치 로그", padding="5")
        log_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))

        # Progress bar
        self.progress = ttk.Progressbar(log_frame, mode='determinate', length=400)
        self.progress.pack(fill=tk.X, pady=(0, 5))

        self.progress_label = ttk.Label(log_frame, text="준비 완료")
        self.progress_label.pack(fill=tk.X)

        # Log text area
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=(5, 0))

    def log(self, message, level="INFO"):
        """Add a log message to the log text area"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{timestamp}] [{level}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)
        self.root.update_idletasks()

    def check_adb_availability(self):
        """Check if ADB is available (bundled or system)"""
        try:
            # First try bundled ADB
            if self.adb_path.exists():
                result = subprocess.run([str(self.adb_path), "version"],
                                       capture_output=True, text=True, timeout=5,
                                       creationflags=SUBPROCESS_FLAGS)
                if result.returncode == 0:
                    self.log(f"✓ 내장 ADB 사용 가능 ({self.adb_dir})")
                    return True

            # Fallback to system PATH
            result = subprocess.run(["adb", "version"], capture_output=True, text=True, timeout=5,
                                   creationflags=SUBPROCESS_FLAGS)
            if result.returncode == 0:
                self.log("✓ 시스템 ADB 사용 가능")
                # Update path to use system adb
                self.adb_path = Path("adb")
                return True
            else:
                self.log("ADB를 찾을 수 없음", "ERROR")
                messagebox.showerror("ADB를 찾을 수 없음",
                                   "ADB가 설치되지 않았거나 찾을 수 없습니다.")
                return False
        except Exception as e:
            self.log(f"ADB 확인 오류: {str(e)}", "ERROR")
            messagebox.showerror("ADB 오류", f"ADB 확인 실패: {str(e)}")
            return False

    def auto_detect_ip_range(self):
        """Automatically detect the local network IP range"""
        try:
            # Method 1: Connect to external address to determine local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(0.1)
            try:
                # Doesn't actually connect, just determines which interface would be used
                s.connect(('8.8.8.8', 80))
                local_ip = s.getsockname()[0]
                s.close()
            except:
                s.close()
                # Method 2: Get hostname and resolve it
                local_ip = socket.gethostbyname(socket.gethostname())

            # Extract network prefix (first three octets)
            if local_ip and local_ip != '127.0.0.1':
                ip_parts = local_ip.split('.')
                if len(ip_parts) == 4:
                    network_prefix = '.'.join(ip_parts[:3])
                    self.ip_range_var.set(network_prefix)
                    self.log(f"IP 범위 자동 감지: {network_prefix}.* (현재 IP: {local_ip})")
                    return network_prefix

            # Fallback: try all network interfaces
            import socket as sock
            hostname = sock.gethostname()
            local_ips = sock.getaddrinfo(hostname, None)

            for ip_info in local_ips:
                ip = ip_info[4][0]
                if ip.startswith('192.168.') or ip.startswith('10.') or ip.startswith('172.'):
                    ip_parts = ip.split('.')
                    if len(ip_parts) == 4:
                        network_prefix = '.'.join(ip_parts[:3])
                        self.ip_range_var.set(network_prefix)
                        self.log(f"IP 범위 자동 감지: {network_prefix}.* (현재 IP: {ip})")
                        return network_prefix

            # If no suitable IP found, keep default
            self.log("IP 범위를 자동 감지할 수 없음, 기본값 사용: 192.168.1", "WARNING")
            self.ip_range_var.set("192.168.1")

        except Exception as e:
            self.log(f"IP 범위 자동 감지 실패: {str(e)}", "WARNING")
            self.log("기본 IP 범위 사용: 192.168.1")
            self.ip_range_var.set("192.168.1")

    def scan_network(self):
        """Scan the network for Android devices on ports 5555 and 1206"""
        if self.scanning:
            return

        self.scanning = True
        self.scan_btn.config(state=tk.DISABLED)
        self.scan_progress.start()
        self.log("네트워크 스캔 시작...")

        # Clear existing devices
        for widget in self.device_list_frame.winfo_children():
            widget.destroy()
        self.devices.clear()
        self.device_vars.clear()

        def scan_thread():
            ip_range = self.ip_range_var.get()
            ports = [5555, 1206]
            found_devices = []

            print(f"[DEBUG] Starting scan on {ip_range}.* with ports {ports}")

            for i in range(1, 255):
                ip = f"{ip_range}.{i}"
                for port in ports:
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(0.1)
                        result = sock.connect_ex((ip, port))
                        sock.close()

                        if result == 0:
                            print(f"[DEBUG] Port open at {ip}:{port}")
                            self.log(f"디바이스 발견: {ip}:{port}")
                            device = AndroidDevice(ip, port)
                            found_devices.append(device)
                            print(f"[DEBUG] Device added to found_devices: {device}")
                    except Exception as e:
                        print(f"[DEBUG] Socket error at {ip}:{port} - {e}")
                        pass

            print(f"[DEBUG] Port scan complete. Found {len(found_devices)} potential devices")

            # Connect to found devices and get info
            adb_exe = str(self.adb_path) if self.adb_path.exists() else "adb"

            for device in found_devices:
                print(f"[DEBUG] Attempting to connect to {device.ip}:{device.port}")
                try:
                    # Try to connect
                    result = subprocess.run(
                        [adb_exe, "connect", f"{device.ip}:{device.port}"],
                        capture_output=True, text=True, timeout=10,
                        creationflags=SUBPROCESS_FLAGS
                    )
                    print(f"[DEBUG] ADB connect result: {result.stdout.strip()}")

                    if "connected" in result.stdout.lower():
                        device.status = "Connected"
                        print(f"[DEBUG] Device {device.ip}:{device.port} connected successfully")

                        # Get Android version
                        version_result = subprocess.run(
                            [adb_exe, "-s", f"{device.ip}:{device.port}",
                             "shell", "getprop", "ro.build.version.release"],
                            capture_output=True, text=True, timeout=5,
                            creationflags=SUBPROCESS_FLAGS
                        )
                        device.version = version_result.stdout.strip()
                        print(f"[DEBUG] Device version: {device.version}")

                        # Get device model
                        model_result = subprocess.run(
                            [adb_exe, "-s", f"{device.ip}:{device.port}",
                             "shell", "getprop", "ro.product.model"],
                            capture_output=True, text=True, timeout=5,
                            creationflags=SUBPROCESS_FLAGS
                        )
                        device.model = model_result.stdout.strip()
                        print(f"[DEBUG] Device model: {device.model}")

                        self.devices.append(device)
                        print(f"[DEBUG] Device added to self.devices: {device}")
                        print(f"[DEBUG] Total devices in self.devices: {len(self.devices)}")
                        self.log(f"연결됨: {device}")
                except Exception as e:
                    print(f"[DEBUG] Exception connecting to {device.ip}:{device.port} - {str(e)}")
                    self.log(f"연결 실패 {device.ip}:{device.port} - {str(e)}", "ERROR")

            print(f"[DEBUG] All connections complete. Total devices: {len(self.devices)}")
            print(f"[DEBUG] Devices list: {[str(d) for d in self.devices]}")

            # Update UI
            print("[DEBUG] Scheduling UI update...")
            self.root.after(0, self.update_device_list)
            self.root.after(0, lambda: self.scan_progress.stop())
            self.root.after(0, lambda: self.scan_btn.config(state=tk.NORMAL))
            self.scanning = False
            self.log(f"스캔 완료. 발견된 디바이스: {len(self.devices)}개")
            print(f"[DEBUG] Scan thread complete")

        threading.Thread(target=scan_thread, daemon=True).start()

    def update_device_list(self):
        """Update the device list UI"""
        print(f"[DEBUG] update_device_list called")
        print(f"[DEBUG] Number of devices: {len(self.devices)}")
        print(f"[DEBUG] Devices: {[str(d) for d in self.devices]}")

        for widget in self.device_list_frame.winfo_children():
            widget.destroy()
        self.device_vars.clear()

        if not self.devices:
            print("[DEBUG] No devices to display - returning early")
            self.log("표시할 디바이스 없음")
            return

        self.log(f"디바이스 목록 업데이트 중: {len(self.devices)}개")
        print(f"[DEBUG] Creating UI elements for {len(self.devices)} devices")

        for idx, device in enumerate(self.devices):
            print(f"[DEBUG] Creating UI for device {idx}: {device}")
            frame = ttk.Frame(self.device_list_frame)
            frame.pack(fill=tk.X, pady=2)
            print(f"[DEBUG] Frame created and packed")

            var = tk.BooleanVar(value=False)
            self.device_vars.append((device, var))
            print(f"[DEBUG] BooleanVar created, device_vars length: {len(self.device_vars)}")

            cb = ttk.Checkbutton(frame, variable=var,
                               text=str(device),
                               command=self.update_button_states)
            cb.pack(side=tk.LEFT, fill=tk.X, expand=True)
            print(f"[DEBUG] Checkbutton created and packed: {str(device)}")

            # Status label
            status_label = ttk.Label(frame, text=device.status, width=15)
            status_label.pack(side=tk.RIGHT)
            print(f"[DEBUG] Status label created: {device.status}")

        print("[DEBUG] All UI elements created")

        # Force update the canvas scroll region
        self.device_list_frame.update_idletasks()
        self.device_list_canvas.configure(scrollregion=self.device_list_canvas.bbox("all"))
        print(f"[DEBUG] Canvas scroll region updated: {self.device_list_canvas.bbox('all')}")

        self.log(f"디바이스 목록 업데이트 완료 - {len(self.device_vars)}개 표시됨")
        print(f"[DEBUG] Calling update_button_states...")
        self.update_button_states()
        print(f"[DEBUG] update_device_list complete")

    def update_button_states(self):
        """Update button states based on device selection"""
        any_selected = any(var.get() for _, var in self.device_vars)
        self.install_btn.config(state=tk.NORMAL if any_selected else tk.DISABLED)
        self.backup_btn.config(state=tk.NORMAL if any_selected else tk.DISABLED)
        # Scrcpy button should be enabled if device selected OR scrcpy is running
        scrcpy_running = self.scrcpy_process and self.scrcpy_process.poll() is None
        self.scrcpy_btn.config(state=tk.NORMAL if (any_selected or scrcpy_running) else tk.DISABLED)

    def start_installation(self):
        """Start installation process on selected devices"""
        if self.installing:
            return

        selected_devices = [device for device, var in self.device_vars if var.get()]
        if not selected_devices:
            messagebox.showwarning("디바이스 없음", "최소 1개 이상의 디바이스를 선택해주세요")
            return

        # Check if files exist
        if not self.files_dir.exists():
            messagebox.showerror("파일을 찾을 수 없음",
                               f"설치 파일을 찾을 수 없음: {self.files_dir}")
            return

        self.installing = True
        self.install_btn.config(state=tk.DISABLED)
        self.backup_btn.config(state=tk.DISABLED)

        def install_thread():
            total_devices = len(selected_devices)

            for idx, device in enumerate(selected_devices):
                try:
                    self.log(f"\n{'='*60}")
                    self.log(f"디바이스에 설치 중 {idx+1}/{total_devices}: {device.ip}")
                    self.log(f"{'='*60}\n")

                    # Update progress
                    progress_pct = (idx / total_devices) * 100
                    self.root.after(0, lambda p=progress_pct: self.progress.config(value=p))
                    self.root.after(0, lambda d=device:
                                  self.progress_label.config(text=f"설치 중: to {d.ip}..."))

                    # Install to device first (scrcpy will be started after root/reboot)
                    self.install_to_device(device)

                    self.log(f"✅ 설치 완료: {device.ip}")

                    # Update device status
                    for d, var in self.device_vars:
                        if d.ip == device.ip:
                            self.root.after(0, lambda: self.update_device_list())
                            break

                except Exception as e:
                    self.log(f"❌ 설치 실패: {device.ip}: {str(e)}", "ERROR")

            # Complete
            self.root.after(0, lambda: self.progress.config(value=100))
            self.root.after(0, lambda: self.progress_label.config(text="설치 완료"))
            self.root.after(0, lambda: self.install_btn.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.backup_btn.config(state=tk.NORMAL))
            self.installing = False
            self.log("\n🎉 모든 설치 완료!")

            # Keep scrcpy running for last device so user can verify
            self.log("Scrcpy가 마지막 디바이스에서 계속 실행 중 - 완료되면 'Scrcpy 중지'를 클릭하세요")

        threading.Thread(target=install_thread, daemon=True).start()

    def install_to_device(self, device):
        """Install apps and files to a specific device"""
        device_addr = f"{device.ip}:{device.port}"
        adb_exe = str(self.adb_path) if self.adb_path.exists() else "adb"

        # Step 1: Root access
        self.log(f"[1/10] 루트 권한 요청 중...")
        try:
            result = self.run_adb_command(device_addr, ["root"])
            if "restarting" in result:
                self.log("디바이스 재시작 대기 중...")
                time.sleep(3)

                # Reconnect to the device
                try:
                    adb_exe = str(self.adb_path) if self.adb_path.exists() else "adb"
                    subprocess.run([adb_exe, "connect", device_addr],
                                 capture_output=True, text=True, timeout=5,
                                 creationflags=SUBPROCESS_FLAGS)
                except:
                    pass

                # Wait for this specific device to be ready
                max_wait = 30
                for i in range(0, max_wait, 2):
                    try:
                        result = subprocess.run(
                            [adb_exe, "-s", device_addr, "get-state"],
                            capture_output=True, text=True, timeout=2,
                            creationflags=SUBPROCESS_FLAGS
                        )
                        if result.returncode == 0 and "device" in result.stdout:
                            self.log(f"디바이스 준비 완료: {i+2}초")
                            break
                    except:
                        pass
                    time.sleep(2)
        except Exception as e:
            self.log(f"루트 접근: {str(e)}", "WARNING")

        # Step 2: Install APKs
        self.log(f"[2/10] APK 파일 설치 중...")
        apk_dir = self.files_dir / "apk_files"
        for apk in self.apk_files:
            apk_path = apk_dir / apk
            if apk_path.exists():
                self.log(f"설치 중: {apk}...")
                self.run_adb_command(device_addr, ["install", "-r", str(apk_path)])
            else:
                self.log(f"APK를 찾을 수 없음: {apk}", "WARNING")

        # Step 3: Grant permissions
        self.log(f"[3/10] 앱 권한 부여 중...")
        permissions = [
            "android.permission.WRITE_SECURE_SETTINGS",
            "android.permission.ACCESS_FINE_LOCATION",
            "android.permission.ACCESS_COARSE_LOCATION",
            "android.permission.READ_EXTERNAL_STORAGE",
            "android.permission.WRITE_EXTERNAL_STORAGE",
            "android.permission.CAMERA"
        ]
        for perm in permissions:
            try:
                self.run_adb_command(device_addr,
                                   ["shell", "pm", "grant", self.app_package, perm])
            except:
                pass  # Some permissions might not be available on all Android versions

        # Step 4: Launch app to create directories
        self.log(f"[4/10] 앱 초기화 시작...")
        self.run_adb_command(device_addr,
                           ["shell", "monkey", "-p", self.app_package,
                            "-c", "android.intent.category.LAUNCHER", "1"])
        time.sleep(5)

        # NOW start scrcpy - device is stable after root restart and app launch
        self.log(f"설치 모니터링을 위해 scrcpy 시작...")
        self.root.after(0, lambda d=device: self.auto_start_scrcpy(d))
        time.sleep(3)  # Give scrcpy time to embed

        # Step 5: Push files
        android_ver = device.version or "Unknown"
        self.log(f"[5/10] 파일 전송 중... (Android {android_ver})")
        source = self.get_installation_source()

        # Track transfer results for summary
        transfer_results = {
            'sdcard': {'status': None, 'count': 0, 'error': None},
            'app_files': {'status': None, 'count': 0, 'error': None},
            'database': {'status': None, 'error': None},
            'prefs': {'status': None, 'error': None},
            'ownership': {'status': None, 'owner': None, 'error': None},
        }

        # Ensure device is connected before file transfer
        self.ensure_device_connection(device_addr)

        # Push files to sdcard with retry logic
        sdcard_src = source / "sdcard"
        if sdcard_src.exists():
            files_src = sdcard_src / "files"
            if files_src.exists():
                # Count files
                file_count = sum(1 for _ in files_src.rglob('*') if _.is_file())
                self.log(f"  SD카드 전송 중... ({file_count}개 파일)")

                # Retry logic for file transfer
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        # Ensure connection before each attempt
                        if attempt > 0:
                            err_msg, solution = self.get_error_message(str(transfer_results['sdcard']['error']))
                            self.log(f"  ⚠ SD카드 실패: {err_msg} (재시도 {attempt + 1}/{max_retries})")
                            self.log(f"    → 재연결 중...")
                            self.ensure_device_connection(device_addr)
                            time.sleep(2)

                        print(f"[DEBUG] Pushing {files_src} to /sdcard/Android/data/{self.app_package}/")
                        result = subprocess.run(
                            [adb_exe, "-s", device_addr, "push", str(files_src),
                             f"/sdcard/Android/data/{self.app_package}/"],
                            capture_output=True, text=True, timeout=600,
                            creationflags=SUBPROCESS_FLAGS
                        )
                        if result.returncode != 0:
                            error_msg = result.stderr if result.stderr else result.stdout
                            print(f"[DEBUG] Push failed: {error_msg}")
                            raise Exception(error_msg)
                        self.log(f"  ✓ SD카드: {file_count}개 파일")
                        transfer_results['sdcard'] = {'status': 'success', 'count': file_count, 'error': None}
                        break
                    except subprocess.TimeoutExpired:
                        transfer_results['sdcard']['error'] = 'timeout'
                        if attempt == max_retries - 1:
                            self.log(f"  ⚠ SD카드 최종 실패: 시간 초과", "WARNING")
                            self.log(f"    → 해결: 네트워크 확인", "WARNING")
                            transfer_results['sdcard']['status'] = 'failed'
                    except Exception as e:
                        transfer_results['sdcard']['error'] = str(e)
                        if attempt == max_retries - 1:
                            err_msg, solution = self.get_error_message(str(e))
                            self.log(f"  ⚠ SD카드 최종 실패: {err_msg}", "WARNING")
                            self.log(f"    → 해결: {solution}", "WARNING")
                            transfer_results['sdcard']['status'] = 'failed'

        # Push data files (database, preferences, app files)
        data_src = source / "data"
        if data_src.exists():
            # Ensure device is still connected before continuing
            self.ensure_device_connection(device_addr)

            try:
                self.run_adb_command(device_addr, ["remount"])
            except:
                pass

            # Create necessary directories first
            try:
                self.run_adb_command(device_addr,
                    ["shell", "mkdir", "-p", f"/data/data/{self.app_package}/files"])
                self.run_adb_command(device_addr,
                    ["shell", "mkdir", "-p", f"/data/data/{self.app_package}/databases"])
                self.run_adb_command(device_addr,
                    ["shell", "mkdir", "-p", f"/data/data/{self.app_package}/shared_prefs"])
                self.run_adb_command(device_addr,
                    ["shell", "mkdir", "-p", f"/sdcard/Android/data/{self.app_package}/files"])
            except Exception as e:
                err_msg, _ = self.get_error_message(str(e))
                self.log(f"  ⚠ 디렉토리 생성 실패: {err_msg}", "WARNING")

            # Push app files to /data/data
            data_files = data_src / "files"
            if data_files.exists():
                file_count = sum(1 for _ in data_files.rglob('*') if _.is_file())
                try:
                    self.run_adb_command(device_addr,
                                       ["push", str(data_files) + "/.",
                                        f"/data/data/{self.app_package}/files/"],
                                       timeout=300)
                    self.log(f"  ✓ 앱 파일: {file_count}개")
                    transfer_results['app_files'] = {'status': 'success', 'count': file_count, 'error': None}
                except Exception as e:
                    err_msg, solution = self.get_error_message(str(e))
                    self.log(f"  ⚠ 앱 파일 실패: {err_msg}", "WARNING")
                    self.log(f"    → 해결: {solution}", "WARNING")
                    transfer_results['app_files'] = {'status': 'failed', 'count': 0, 'error': str(e)}

            # Push database
            db_file = data_src / "MainDatabase.db"
            if db_file.exists():
                try:
                    self.run_adb_command(device_addr,
                                       ["push", str(db_file),
                                        f"/data/data/{self.app_package}/databases/"],
                                       timeout=120)
                    self.log(f"  ✓ DB: MainDatabase.db")
                    transfer_results['database'] = {'status': 'success', 'error': None}
                except Exception as e:
                    err_msg, solution = self.get_error_message(str(e))
                    self.log(f"  ⚠ DB 실패: {err_msg}", "WARNING")
                    self.log(f"    → 해결: {solution}", "WARNING")
                    transfer_results['database'] = {'status': 'failed', 'error': str(e)}

            # Push preferences
            prefs_file = data_src / f"{self.app_package}_preferences.xml"
            if prefs_file.exists():
                try:
                    self.run_adb_command(device_addr,
                                       ["push", str(prefs_file),
                                        f"/data/data/{self.app_package}/shared_prefs/"],
                                       timeout=60)
                    self.log(f"  ✓ 설정: {prefs_file.name}")
                    transfer_results['prefs'] = {'status': 'success', 'error': None}
                except Exception as e:
                    err_msg, solution = self.get_error_message(str(e))
                    self.log(f"  ⚠ 설정 실패: {err_msg}", "WARNING")
                    self.log(f"    → 해결: {solution}", "WARNING")
                    transfer_results['prefs'] = {'status': 'failed', 'error': str(e)}

        # Step 6: Fix ownership (always run, not just Android 12+)
        self.log(f"[6/10] 파일 소유권 수정 중...")
        try:
            # Get app owner
            result = self.run_adb_command(device_addr,
                                        ["shell", "stat", "-c", "%U",
                                         f"/data/data/{self.app_package}"])
            app_owner = result.strip()

            if app_owner and app_owner != "unknown":
                self.run_adb_command(device_addr,
                                   ["shell", "chown", "-R",
                                    f"{app_owner}:{app_owner}",
                                    f"/data/data/{self.app_package}"])
                self.run_adb_command(device_addr,
                                   ["shell", "chown", "-R",
                                    f"{app_owner}:{app_owner}",
                                    f"/sdcard/Android/data/{self.app_package}"])
                self.log(f"  ✓ 소유권: {app_owner}")
                transfer_results['ownership'] = {'status': 'success', 'owner': app_owner, 'error': None}
            else:
                self.log(f"  ⚠ 소유권 실패: 앱 소유자 불명", "WARNING")
                self.log(f"    → 해결: 앱 설치 확인", "WARNING")
                transfer_results['ownership'] = {'status': 'failed', 'owner': None, 'error': 'unknown owner'}
        except Exception as e:
            err_msg, solution = self.get_error_message(str(e))
            self.log(f"  ⚠ 소유권 실패: {err_msg}", "WARNING")
            self.log(f"    → 해결: {solution}", "WARNING")
            transfer_results['ownership'] = {'status': 'failed', 'owner': None, 'error': str(e)}

        # Verification: Check if key files exist on device
        self.log(f"  파일 검증 중...")
        verified_count = 0
        missing_files = []
        try:
            # Check database
            result = self.run_adb_command(device_addr,
                                        ["shell", "ls", f"/data/data/{self.app_package}/databases/MainDatabase.db"])
            if "MainDatabase.db" in result:
                verified_count += 1
            else:
                missing_files.append("DB")
        except:
            missing_files.append("DB")

        try:
            # Check app files directory
            result = self.run_adb_command(device_addr,
                                        ["shell", "ls", f"/data/data/{self.app_package}/files/"])
            if result.strip():
                verified_count += 1
            else:
                missing_files.append("앱 파일")
        except:
            missing_files.append("앱 파일")

        if missing_files:
            self.log(f"  ⚠ 검증: {len(missing_files)}개 항목 누락 ({', '.join(missing_files)})", "WARNING")
        else:
            self.log(f"  ✓ 검증: 주요 파일 확인됨")

        # Transfer Summary
        success_count = sum(1 for k, v in transfer_results.items() if v.get('status') == 'success')
        failed_count = sum(1 for k, v in transfer_results.items() if v.get('status') == 'failed')
        total_count = success_count + failed_count

        if failed_count > 0:
            self.log(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            self.log(f"⚠ 전송 결과: {success_count}/{total_count} 성공")
            for key, val in transfer_results.items():
                if val.get('status') == 'failed':
                    name_map = {'sdcard': 'SD카드', 'app_files': '앱 파일', 'database': 'DB', 'prefs': '설정', 'ownership': '소유권'}
                    err_msg, _ = self.get_error_message(str(val.get('error', '')))
                    self.log(f"  - {name_map.get(key, key)}: 실패 ({err_msg})")
            self.log(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        # Step 7: Force stop app
        self.log(f"[7/10] 앱 중지 중...")
        self.run_adb_command(device_addr, ["shell", "am", "force-stop", self.app_package])

        # Step 8: Set language and keyboard
        self.log(f"[8/10] 시스템 언어 및 키보드 설정 중...")
        korean_kb = "com.google.android.inputmethod.korean/.KoreanIme"

        # Set language
        self.run_adb_command(device_addr,
                           ["shell", "settings", "put", "global",
                            "system_locales", "ko-KR"])
        self.run_adb_command(device_addr,
                           ["shell", "settings", "put", "system",
                            "system_locales", "ko-KR"])
        self.run_adb_command(device_addr,
                           ["shell", "setprop", "persist.sys.language", "ko"])
        self.run_adb_command(device_addr,
                           ["shell", "setprop", "persist.sys.country", "KR"])

        # Set keyboard
        self.run_adb_command(device_addr, ["shell", "ime", "enable", korean_kb])
        self.run_adb_command(device_addr, ["shell", "ime", "set", korean_kb])

        # Step 9: Reboot
        self.log(f"[9/10] 디바이스 재부팅 중...")
        self.run_adb_command(device_addr, ["reboot"])

        self.log("디바이스 재부팅 대기 중...")
        time.sleep(5)  # Initial wait for reboot to start

        # Wait for this specific device to come back online
        self.log("디바이스 온라인 대기 중...")
        max_wait = 60  # Wait up to 60 seconds
        wait_interval = 2
        for i in range(0, max_wait, wait_interval):
            try:
                # Try to get device state
                result = subprocess.run(
                    [adb_exe, "-s", device_addr, "get-state"],
                    capture_output=True, text=True, timeout=2,
                    creationflags=SUBPROCESS_FLAGS
                )
                if result.returncode == 0 and "device" in result.stdout:
                    self.log(f"디바이스 온라인 복귀: {i+wait_interval}초")
                    break
            except:
                pass
            time.sleep(wait_interval)
        else:
            self.log("디바이스 재부팅이 예상보다 오래 걸림, 그래도 계속 진행...", "WARNING")

        # Step 10: Set home app
        self.log(f"[10/10] 홈 앱 설정 중...")
        time.sleep(5)  # Wait for system to stabilize

        # Re-enable keyboard after reboot
        self.run_adb_command(device_addr, ["shell", "ime", "enable", korean_kb])
        self.run_adb_command(device_addr, ["shell", "ime", "set", korean_kb])

        # Set as home app
        home_component = f"{self.app_package}/.MainActivity"
        self.run_adb_command(device_addr,
                           ["shell", "cmd", "package", "set-home-activity", home_component])

    def get_installation_source(self):
        """Get the installation source directory based on user selection"""
        if self.install_source_var.get() == "backup":
            selected = self.backup_combo.get()
            if selected:
                return self.backup_dir / selected
        return self.files_dir

    def start_backup(self):
        """Backup apps and files from selected device"""
        selected_devices = [device for device, var in self.device_vars if var.get()]
        if not selected_devices:
            messagebox.showwarning("디바이스 없음", "백업할 디바이스를 선택해주세요")
            return

        if len(selected_devices) > 1:
            messagebox.showwarning("여러 디바이스 선택됨",
                                 "백업할 디바이스를 1개만 선택해주세요")
            return

        device = selected_devices[0]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{device.ip.replace('.', '_')}_{timestamp}"
        backup_path = self.backup_dir / backup_name
        backup_path.mkdir(exist_ok=True)

        def backup_thread():
            try:
                self.log(f"\n{'='*60}")
                self.log(f"백업 시작: {device.ip}")
                self.log(f"백업 위치: {backup_path}")
                self.log(f"{'='*60}\n")

                device_addr = f"{device.ip}:{device.port}"

                # Request root access first (needed for /data/data access)
                self.log("[1/6] 루트 권한 요청 중...")
                try:
                    result = self.run_adb_command(device_addr, ["root"])
                    if "restarting" in result:
                        self.log("디바이스 재시작 대기 중...")
                        time.sleep(3)
                        # Reconnect
                        adb_exe = str(self.adb_path) if self.adb_path.exists() else "adb"
                        subprocess.run([adb_exe, "connect", device_addr],
                                     capture_output=True, text=True, timeout=5,
                                     creationflags=SUBPROCESS_FLAGS)
                        # Wait for device to be ready
                        for i in range(15):
                            try:
                                result = subprocess.run(
                                    [adb_exe, "-s", device_addr, "get-state"],
                                    capture_output=True, text=True, timeout=2,
                                    creationflags=SUBPROCESS_FLAGS
                                )
                                if result.returncode == 0 and "device" in result.stdout:
                                    self.log(f"디바이스 준비 완료: {i+2}초")
                                    break
                            except:
                                pass
                            time.sleep(2)
                except Exception as e:
                    self.log(f"루트 접근: {str(e)}", "WARNING")

                # Create directory structure (matching install_files structure)
                apk_dir = backup_path / "apk_files"
                apk_dir.mkdir(exist_ok=True)

                sdcard_dir = backup_path / "sdcard"
                sdcard_dir.mkdir(exist_ok=True)

                data_dir = backup_path / "data"
                data_dir.mkdir(exist_ok=True)

                # Pull APK
                self.log("[2/6] APK 백업 중...")
                apk_path = self.run_adb_command(device_addr,
                                              ["shell", "pm", "path", self.app_package])
                if apk_path:
                    apk_path = apk_path.replace("package:", "").strip()
                    self.run_adb_command(device_addr,
                                       ["pull", apk_path,
                                        str(apk_dir / "EightPresso.apk")])
                    self.log(f"✓ APK 백업 완료: {apk_dir / 'EightPresso.apk'}")

                # Pull files from sdcard
                self.log("[3/6] /sdcard에서 파일 백업 중...")
                try:
                    result = self.run_adb_command(device_addr,
                                       ["pull",
                                        f"/sdcard/Android/data/{self.app_package}/files",
                                        str(sdcard_dir)])
                    self.log(f"✓ SD카드 파일 백업 완료")
                except Exception as e:
                    self.log(f"⚠ SD카드 백업 실패: {str(e)}", "WARNING")

                # Pull files from /data/data
                self.log("[4/6] /data/data에서 앱 파일 백업 중...")
                try:
                    result = self.run_adb_command(device_addr,
                                       ["pull",
                                        f"/data/data/{self.app_package}/files",
                                        str(data_dir)])
                    self.log(f"✓ 앱 파일 백업 완료")
                except Exception as e:
                    self.log(f"⚠ 앱 파일 백업 실패: {str(e)}", "WARNING")

                # Pull database
                self.log("[5/6] 데이터베이스 백업 중...")
                try:
                    result = self.run_adb_command(device_addr,
                                       ["pull",
                                        f"/data/data/{self.app_package}/databases/MainDatabase.db",
                                        str(data_dir / "MainDatabase.db")])
                    self.log(f"✓ 데이터베이스 백업 완료")
                except Exception as e:
                    self.log(f"⚠ 데이터베이스 백업 실패: {str(e)}", "WARNING")

                # Pull preferences
                self.log("[6/6] 환경설정 백업 중...")
                try:
                    result = self.run_adb_command(device_addr,
                                       ["pull",
                                        f"/data/data/{self.app_package}/shared_prefs/{self.app_package}_preferences.xml",
                                        str(data_dir / f"{self.app_package}_preferences.xml")])
                    self.log(f"✓ 환경설정 백업 완료")
                except Exception as e:
                    self.log(f"⚠ 환경설정 백업 실패: {str(e)}", "WARNING")

                # Create backup metadata
                metadata = {
                    "device_ip": device.ip,
                    "device_model": device.model,
                    "android_version": device.version,
                    "timestamp": timestamp,
                    "backup_name": backup_name
                }

                with open(backup_path / "backup_info.json", "w") as f:
                    json.dump(metadata, f, indent=2)

                self.log(f"\n✅ 백업 완료!")
                self.log(f"백업 저장 위치: {backup_path}")

                # Refresh backup list
                self.root.after(0, self.refresh_backup_list)

            except Exception as e:
                self.log(f"❌ 백업 실패: {str(e)}", "ERROR")

        threading.Thread(target=backup_thread, daemon=True).start()

    def refresh_backup_list(self):
        """Refresh the list of available backups"""
        backups = []
        if self.backup_dir.exists():
            for item in self.backup_dir.iterdir():
                if item.is_dir() and item.name.startswith("backup_"):
                    backups.append(item.name)
        backups.sort(reverse=True)
        self.backup_combo['values'] = backups
        if backups:
            self.backup_combo.current(0)

    def cleanup_database_images(self):
        """Clean up orphaned image files from database"""
        db_path = filedialog.askopenfilename(
            title="MainDatabase.db 선택",
            filetypes=[("데이터베이스 파일", "*.db"), ("모든 파일", "*.*")]
        )

        if not db_path:
            return

        image_dir = filedialog.askdirectory(
            title="이미지 파일 디렉토리 선택 (data/files 폴더)"
        )

        if not image_dir:
            return

        def is_hex_hash(filename):
            """Check if filename is a valid hex hash (24+ chars, only hex digits)"""
            # Remove extension if any
            name = filename.split('.')[0]
            # Check if it's at least 24 characters and all hex digits (0-9, a-f)
            if len(name) >= 24:
                try:
                    int(name, 16)  # Try to parse as hex
                    return True
                except ValueError:
                    return False
            return False

        def extract_filename(value):
            """Extract just the filename from a path or return the value if it's already a filename"""
            if not value or not isinstance(value, str):
                return None
            # Remove any path separators (both / and \)
            filename = value.replace('\\', '/').split('/')[-1]
            # Remove extension
            filename = filename.split('.')[0]
            return filename if filename else None

        def cleanup_thread():
            try:
                self.log(f"\n{'='*60}")
                self.log("데이터베이스 이미지 정리 시작")
                self.log(f"데이터베이스: {db_path}")
                self.log(f"이미지 디렉토리: {image_dir}")
                self.log(f"{'='*60}\n")

                image_path = Path(image_dir)

                # STEP 1: Remove non-hex files first
                self.log("단계 1: 비-헥스 해시 파일 제거 중...")
                all_files = list(image_path.iterdir())
                non_hex_files = []

                for file in all_files:
                    if file.is_file() and not is_hex_hash(file.name):
                        non_hex_files.append(file)

                if non_hex_files:
                    self.log(f"발견: {len(non_hex_files)}개의 비-헥스 해시 파일 제거 예정")

                    # Move non-hex files to a separate folder
                    non_hex_dir = image_path / "non_hex_files"
                    non_hex_dir.mkdir(exist_ok=True)

                    for file in non_hex_files:
                        try:
                            shutil.move(str(file), str(non_hex_dir / file.name))
                            self.log(f"비-헥스 파일 제거됨: {file.name}")
                        except Exception as e:
                            self.log(f"이동 오류 {file.name}: {str(e)}", "WARNING")

                    self.log(f"✓ 이동 완료: {len(non_hex_files)}개의 비-헥스 파일 -> {non_hex_dir}\n")
                else:
                    self.log("✓ 모든 파일이 헥스 해시 형식\n")

                # STEP 2: Connect to database and get referenced images
                self.log("단계 2: 데이터베이스에서 이미지 참조 스캔 중...")
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                referenced_images = set()

                tables = ["category", "category_dessert", "product_image"]
                for table in tables:
                    try:
                        cursor.execute(f"SELECT * FROM {table}")
                        rows = cursor.fetchall()

                        count_before = len(referenced_images)

                        # Look for image references in all cells
                        for row in rows:
                            for value in row:
                                if value and isinstance(value, str):
                                    # Extract just the filename from the value
                                    filename = extract_filename(value)
                                    if filename and is_hex_hash(filename):
                                        referenced_images.add(filename)

                        count_after = len(referenced_images)
                        self.log(f"테이블 '{table}': {count_after - count_before}개의 새 참조 발견 (전체: {count_after})")
                    except Exception as e:
                        self.log(f"테이블 읽기 오류: {table}: {str(e)}", "WARNING")

                conn.close()

                self.log(f"\n✓ 데이터베이스의 총 고유 이미지 해시: {len(referenced_images)}\n")

                # STEP 3: Find orphaned files (only checking remaining hex files)
                self.log("단계 3: 고아 이미지 파일 찾기...")
                remaining_files = [f for f in image_path.iterdir() if f.is_file()]
                orphaned_files = []

                for file in remaining_files:
                    if file.is_file():
                        filename_hash = file.name.split('.')[0]

                        if filename_hash not in referenced_images:
                            orphaned_files.append(file)

                self.log(f"발견: {len(orphaned_files)}개의 고아 파일 (전체 {len(remaining_files)}개의 헥스 파일 중)")

                if orphaned_files:
                    # Show some examples
                    self.log("\n고아 파일 예시:")
                    for file in orphaned_files[:5]:
                        self.log(f"  - {file.name}")
                    if len(orphaned_files) > 5:
                        self.log(f"  ... 외 {len(orphaned_files) - 5}개 추가")

                    # Ask for confirmation
                    response = messagebox.askyesno(
                        "삭제 확인",
                        f"발견: {len(orphaned_files)}개의 고아 파일\n\n"
                        f"이 파일들은 데이터베이스에서 참조되지 않습니다.\n\n"
                        f"'deleted_orphans' 폴더로 이동하시겠습니까?"
                    )

                    if response:
                        # Create a deleted folder
                        deleted_dir = image_path / "deleted_orphans"
                        deleted_dir.mkdir(exist_ok=True)

                        for file in orphaned_files:
                            try:
                                shutil.move(str(file), str(deleted_dir / file.name))
                                self.log(f"이동됨: {file.name}")
                            except Exception as e:
                                self.log(f"이동 오류 {file.name}: {str(e)}", "ERROR")

                        self.log(f"\n✅ 정리 완료! 이동됨: {len(orphaned_files)}개 파일 -> {deleted_dir}")
                        messagebox.showinfo("정리 완료",
                                          f"정리 완료!\n\n"
                                          f"- 제거됨: {len(non_hex_files)}개 비-헥스 파일\n"
                                          f"- 이동됨: {len(orphaned_files)}개 고아 파일")
                    else:
                        self.log("사용자가 정리 취소")
                else:
                    self.log("✓ 고아 파일 없음!")
                    messagebox.showinfo("정리 완료", "고아 파일 없음!")

            except Exception as e:
                self.log(f"❌ 정리 실패: {str(e)}", "ERROR")
                messagebox.showerror("정리 오류", f"정리 실패: {str(e)}")

        threading.Thread(target=cleanup_thread, daemon=True).start()

    def auto_start_scrcpy(self, device):
        """Automatically start scrcpy for a specific device (called during installation)"""
        if not HAS_WIN32:
            self.log("Scrcpy 임베드 불가: pywin32 미설치", "WARNING")
            return

        # Stop any existing scrcpy first and wait for complete cleanup
        if self.scrcpy_process or self.scrcpy_monitor_id or self.scrcpy_search_id:
            print("[DEBUG] Stopping existing scrcpy before starting new one...")
            self.stop_scrcpy()
            # Give it time to fully clean up
            time.sleep(1.5)

        device_addr = f"{device.ip}:{device.port}"
        print(f"[DEBUG] Auto-starting embedded scrcpy for {device_addr}")
        self.scrcpy_placeholder.config(text=f"Scrcpy 시작 중: \n{device.ip}...\n잠시 기다려주세요...")

        # Reset user-stopped flag and track current device for auto-reconnect
        self.scrcpy_user_stopped = False
        self.scrcpy_current_device = device
        # Don't reset retry count here - it's reset on successful start

        try:
            # Determine scrcpy executable path
            if self.scrcpy_path.exists():
                scrcpy_exe = str(self.scrcpy_path)
            else:
                scrcpy_exe = "scrcpy"

            # Check if scrcpy is available (longer timeout for first run)
            result = subprocess.run([scrcpy_exe, "--version"], capture_output=True, timeout=10,
                                   creationflags=SUBPROCESS_FLAGS)
            if result.returncode != 0:
                raise FileNotFoundError("scrcpy not working")

            # Create unique window title
            window_title = f"RT1018_EMBED_{int(time.time())}"

            # Start scrcpy with bundled ADB
            adb_exe = str(self.adb_path) if self.adb_path.exists() else "adb"
            cmd = [
                scrcpy_exe,
                "-s", device_addr,
                "--window-title", window_title,
                "--window-borderless",
                "--always-on-top",
                "--window-width", "960",
                "--window-height", "540"
            ]

            # Set environment to use bundled ADB
            env = os.environ.copy()
            if self.adb_dir.exists():
                env["PATH"] = str(self.adb_dir) + os.pathsep + env.get("PATH", "")

            print(f"[DEBUG] Scrcpy command: {' '.join(cmd)}")

            self.scrcpy_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                creationflags=SUBPROCESS_FLAGS
            )

            print(f"[DEBUG] Scrcpy started with PID: {self.scrcpy_process.pid}")
            self.log(f"→ Scrcpy 자동 시작: {device.ip}")
            self.scrcpy_retry_count = 0  # Reset retry count on successful start

            # Wait for window and embed it, store callback ID
            self.scrcpy_search_id = self.root.after(2000, lambda: self.find_and_embed_scrcpy_window(window_title))

            self.scrcpy_btn.config(text="Scrcpy 중지")

        except FileNotFoundError:
            print("[DEBUG] Scrcpy not found")
            self.log("Scrcpy 사용 불가 - 화면 보기 없이 계속", "WARNING")
            self.scrcpy_placeholder.config(text="Scrcpy 사용 불가\n\n설치 중...")
            # Don't retry for missing scrcpy - it won't appear
            self.scrcpy_current_device = None
        except Exception as e:
            print(f"[DEBUG] Exception auto-starting scrcpy: {str(e)}")
            self.scrcpy_retry_count += 1
            # Retry after delay if not user-stopped and under max retries (device might be rebooting)
            if not self.scrcpy_user_stopped and self.scrcpy_current_device and self.scrcpy_retry_count < self.scrcpy_max_retries:
                self.log(f"Scrcpy 연결 재시도 중... ({self.scrcpy_retry_count}/{self.scrcpy_max_retries})", "WARNING")
                self.scrcpy_placeholder.config(text=f"Scrcpy 연결 재시도 중...\n({self.scrcpy_retry_count}/{self.scrcpy_max_retries})\n\n잠시 기다려주세요...")
                print(f"[DEBUG] Scheduling scrcpy retry {self.scrcpy_retry_count}/{self.scrcpy_max_retries} in 5 seconds...")
                self.root.after(5000, lambda: self.auto_start_scrcpy(self.scrcpy_current_device))
            else:
                self.log(f"Scrcpy 시작 실패: {str(e)}", "WARNING")
                self.scrcpy_placeholder.config(text="Scrcpy 연결 실패\n\n'Scrcpy 시작' 버튼을\n클릭하세요")
                self.scrcpy_current_device = None
                self.scrcpy_retry_count = 0

    def toggle_scrcpy(self):
        """Toggle embedded scrcpy screen mirroring"""
        if self.scrcpy_process and self.scrcpy_process.poll() is None:
            # Scrcpy is running, stop it (user-initiated)
            print("[DEBUG] Stopping scrcpy (user-initiated)...")
            self.scrcpy_user_stopped = True  # Mark as user-intended stop
            self.stop_scrcpy()
        else:
            # Start scrcpy
            if not HAS_WIN32:
                messagebox.showerror("의존성 누락",
                                   "scrcpy 임베드를 위해 pywin32가 필요합니다.\n\npip install pywin32로 설치하세요")
                self.log("Scrcpy 임베드 불가: pywin32 미설치", "ERROR")
                return

            selected_devices = [device for device, var in self.device_vars if var.get()]
            if not selected_devices:
                messagebox.showwarning("디바이스 없음", "먼저 디바이스를 선택해주세요")
                return

            device = selected_devices[0]
            self.auto_start_scrcpy(device)

    def find_and_embed_scrcpy_window(self, window_title):
        """Find scrcpy window and embed it in the frame"""
        # Clear the search callback ID since we're now executing
        self.scrcpy_search_id = None

        if not HAS_WIN32:
            return

        print(f"[DEBUG] Looking for scrcpy window: {window_title}")

        # Find the scrcpy window
        hwnd = win32gui.FindWindow(None, window_title)

        if hwnd:
            print(f"[DEBUG] Found scrcpy window! HWND: {hwnd}")
            self.scrcpy_hwnd = hwnd

            # Get the frame's window handle
            frame_hwnd = self.scrcpy_embed_frame.winfo_id()
            print(f"[DEBUG] Embed frame HWND: {frame_hwnd}")

            try:
                # Remove window decorations
                style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
                style &= ~(win32con.WS_CAPTION | win32con.WS_THICKFRAME | win32con.WS_MINIMIZE |
                          win32con.WS_MAXIMIZE | win32con.WS_SYSMENU)
                win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, style)

                # Set parent to our frame
                win32gui.SetParent(hwnd, frame_hwnd)

                # Resize and position
                print("[DEBUG] Positioning scrcpy window...")
                win32gui.SetWindowPos(
                    hwnd,
                    win32con.HWND_TOP,
                    0, 0,  # Position
                    960, 540,  # Size
                    win32con.SWP_SHOWWINDOW
                )

                self.log("✓ Scrcpy 임베드 성공!", "SUCCESS")
                print("[DEBUG] Scrcpy embedded successfully!")

                # Hide placeholder
                self.scrcpy_placeholder.place_forget()

                # Monitor the embedded window and store callback ID
                self.scrcpy_monitor_id = self.root.after(1000, self.monitor_embedded_scrcpy)

            except Exception as e:
                print(f"[DEBUG] Failed to embed: {str(e)}")
                self.log(f"Scrcpy 임베드 실패: {str(e)}", "ERROR")
                self.scrcpy_placeholder.config(text=f"임베드 실패:\n{str(e)}")

        else:
            print("[DEBUG] Window not found yet, retrying...")
            # Try again
            if self.scrcpy_process and self.scrcpy_process.poll() is None:
                # Store the callback ID for the retry
                self.scrcpy_search_id = self.root.after(1000, lambda: self.find_and_embed_scrcpy_window(window_title))
            else:
                # Scrcpy process died - trigger retry if not user-stopped
                print("[DEBUG] Scrcpy process died")
                self.cleanup_scrcpy()

                self.scrcpy_retry_count += 1
                if not self.scrcpy_user_stopped and self.scrcpy_current_device and self.scrcpy_retry_count < self.scrcpy_max_retries:
                    self.log(f"Scrcpy 프로세스 종료 - 재시도 중... ({self.scrcpy_retry_count}/{self.scrcpy_max_retries})", "WARNING")
                    self.scrcpy_placeholder.config(text=f"Scrcpy 재연결 중...\n({self.scrcpy_retry_count}/{self.scrcpy_max_retries})\n\n잠시 기다려주세요...")
                    print(f"[DEBUG] Scheduling scrcpy retry {self.scrcpy_retry_count}/{self.scrcpy_max_retries} in 5 seconds...")
                    self.root.after(5000, lambda: self.auto_start_scrcpy(self.scrcpy_current_device))
                else:
                    self.log("Scrcpy 프로세스 시작 실패", "ERROR")
                    self.scrcpy_placeholder.config(text="Scrcpy 연결 실패\n\n'Scrcpy 시작' 버튼을\n클릭하세요")
                    self.scrcpy_current_device = None
                    self.scrcpy_retry_count = 0

    def monitor_embedded_scrcpy(self):
        """Monitor the embedded scrcpy window and process"""
        # Clear the callback ID since we're now executing
        self.scrcpy_monitor_id = None

        if self.scrcpy_process:
            poll = self.scrcpy_process.poll()
            if poll is None:
                # Still running - keep window positioned
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

                # Schedule next check and store the callback ID
                self.scrcpy_monitor_id = self.root.after(1000, self.monitor_embedded_scrcpy)
            else:
                # Process ended
                print(f"[DEBUG] Scrcpy stopped (exit code: {poll}), user_stopped={self.scrcpy_user_stopped}")

                # Check if this was user-intended or unexpected disconnection
                if not self.scrcpy_user_stopped and self.scrcpy_current_device:
                    # Unexpected disconnection - auto-reconnect
                    print("[DEBUG] Unexpected scrcpy disconnect - attempting auto-reconnect...")
                    self.log("Scrcpy 연결 끊김 - 자동 재연결 중...", "INFO")
                    self.cleanup_scrcpy()
                    # Schedule reconnect after brief delay
                    self.root.after(2000, lambda: self.auto_start_scrcpy(self.scrcpy_current_device))
                else:
                    # User-intended stop or no device to reconnect to
                    if poll == 2 and self.installing:
                        self.log("Scrcpy 연결 끊김 (디바이스 재부팅 또는 연결 끊김)", "INFO")
                    else:
                        self.log(f"Scrcpy 중지됨 (종료 코드: {poll})", "INFO")
                    self.cleanup_scrcpy()

    def stop_scrcpy(self):
        """Stop scrcpy process"""
        print("[DEBUG] stop_scrcpy called")

        # Cancel any scheduled callbacks first
        if self.scrcpy_monitor_id:
            print(f"[DEBUG] Cancelling monitor callback: {self.scrcpy_monitor_id}")
            self.root.after_cancel(self.scrcpy_monitor_id)
            self.scrcpy_monitor_id = None

        if self.scrcpy_search_id:
            print(f"[DEBUG] Cancelling search callback: {self.scrcpy_search_id}")
            self.root.after_cancel(self.scrcpy_search_id)
            self.scrcpy_search_id = None

        if self.scrcpy_process:
            self.log("Scrcpy 중지 중...")
            try:
                self.scrcpy_process.terminate()
                self.scrcpy_process.wait(timeout=5)
            except:
                print("[DEBUG] Force killing scrcpy...")
                try:
                    self.scrcpy_process.kill()
                    self.scrcpy_process.wait(timeout=2)
                except:
                    pass

            self.cleanup_scrcpy()
        else:
            print("[DEBUG] No scrcpy process to stop")

    def cleanup_scrcpy(self):
        """Cleanup after scrcpy stops"""
        print("[DEBUG] cleanup_scrcpy called")

        # Cancel any remaining callbacks
        if self.scrcpy_monitor_id:
            try:
                self.root.after_cancel(self.scrcpy_monitor_id)
            except:
                pass
            self.scrcpy_monitor_id = None

        if self.scrcpy_search_id:
            try:
                self.root.after_cancel(self.scrcpy_search_id)
            except:
                pass
            self.scrcpy_search_id = None

        self.scrcpy_process = None
        self.scrcpy_hwnd = None

        # Show placeholder again
        self.scrcpy_placeholder.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        # Show different message based on whether auto-reconnect will happen
        if not self.scrcpy_user_stopped and self.scrcpy_current_device:
            self.scrcpy_placeholder.config(text="자동 재연결 중...\n\n잠시 기다려주세요...")
        else:
            self.scrcpy_placeholder.config(text="디바이스를 선택하고 'Scrcpy 시작'을 클릭하세요\n디바이스 화면이 여기에 표시됩니다\n\n(960×540)")
            # Clear device only on user-intended stop
            self.scrcpy_current_device = None

        self.scrcpy_btn.config(text="Scrcpy 시작")
        print("[DEBUG] Scrcpy cleanup complete")

    def get_error_message(self, error_str):
        """Convert ADB error to user-friendly Korean message"""
        error_str = str(error_str).lower()
        error_map = {
            'device offline': ('연결 끊김', '네트워크 확인'),
            'connect failed: closed': ('연결 종료됨', '재시도'),
            'timeout': ('시간 초과', '네트워크 확인'),
            'permission denied': ('권한 거부됨', '루트 권한 확인'),
            'read-only file': ('읽기전용 파일시스템', 'remount 재시도'),
            'no space left': ('저장공간 부족', '디바이스 정리'),
            'not found': ('파일 없음', '설치파일 확인'),
            'unknown': ('앱 소유자 불명', '앱 설치 확인'),
        }
        for key, (msg, solution) in error_map.items():
            if key in error_str:
                return msg, solution
        return '알 수 없는 오류', '로그 확인'

    def run_adb_command(self, device, command, timeout=60):
        """Run an ADB command and return output"""
        adb_exe = str(self.adb_path) if self.adb_path.exists() else "adb"

        if device:
            full_cmd = [adb_exe, "-s", device] + command
        else:
            full_cmd = [adb_exe] + command

        print(f"[DEBUG] ADB: {' '.join(full_cmd)}")
        result = subprocess.run(full_cmd, capture_output=True, text=True, timeout=timeout,
                               creationflags=SUBPROCESS_FLAGS)

        if result.returncode != 0 and result.stderr:
            print(f"[DEBUG] ADB ERROR: {result.stderr}")
            raise Exception(result.stderr)

        if result.stdout:
            print(f"[DEBUG] ADB OUT: {result.stdout[:200]}")

        return result.stdout

    def ensure_device_connection(self, device_addr, max_retries=3):
        """Ensure device is connected, reconnect if necessary"""
        adb_exe = str(self.adb_path) if self.adb_path.exists() else "adb"

        for attempt in range(max_retries):
            try:
                # Check if device is online
                result = subprocess.run(
                    [adb_exe, "-s", device_addr, "get-state"],
                    capture_output=True, text=True, timeout=5,
                    creationflags=SUBPROCESS_FLAGS
                )
                if result.returncode == 0 and "device" in result.stdout:
                    print(f"[DEBUG] Device {device_addr} is online")
                    return True
            except:
                pass

            # Device offline, try to reconnect
            print(f"[DEBUG] Device offline, attempting reconnect ({attempt + 1}/{max_retries})...")
            self.log(f"디바이스 재연결 시도 중... ({attempt + 1}/{max_retries})")

            try:
                subprocess.run(
                    [adb_exe, "connect", device_addr],
                    capture_output=True, text=True, timeout=10,
                    creationflags=SUBPROCESS_FLAGS
                )
                time.sleep(2)

                # Check again
                result = subprocess.run(
                    [adb_exe, "-s", device_addr, "get-state"],
                    capture_output=True, text=True, timeout=5,
                    creationflags=SUBPROCESS_FLAGS
                )
                if result.returncode == 0 and "device" in result.stdout:
                    self.log("✓ 디바이스 재연결 성공")
                    return True
            except:
                pass

            time.sleep(2)

        self.log("디바이스 재연결 실패", "WARNING")
        return False

    def on_closing(self):
        """Handle window closing"""
        if self.scrcpy_process and self.scrcpy_process.poll() is None:
            self.scrcpy_process.terminate()

        # Disconnect all devices
        try:
            adb_exe = str(self.adb_path) if self.adb_path.exists() else "adb"
            subprocess.run([adb_exe, "disconnect"], timeout=5, creationflags=SUBPROCESS_FLAGS)
            subprocess.run([adb_exe, "kill-server"], timeout=5, creationflags=SUBPROCESS_FLAGS)
        except:
            pass

        self.root.destroy()


def main():
    """Main entry point"""
    root = tk.Tk()
    app = RT1018InstallerGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
