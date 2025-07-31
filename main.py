#!/usr/bin/env python3
"""
Web Media Scraper - Portfolio Project
A GUI application for scraping media files from websites with customizable parameters.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
import time
import logging
import re
import os
import queue
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class ToolTip:
    """Modern tooltip class for GUI elements"""
    def __init__(self, widget, text, colors=None):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.colors = colors or {
            'bg': '#1e1f22',
            'text': '#ffffff',
            'border': '#4f545c'
        }
        widget.bind("<Enter>", self.on_enter)
        widget.bind("<Leave>", self.on_leave)
    
    def on_enter(self, event):
        x, y, _, _ = self.widget.bbox("insert") if hasattr(self.widget, 'bbox') else (0, 0, 0, 0)
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(self.tooltip_window, text=self.text, 
                        background=self.colors['bg'], 
                        foreground=self.colors['text'],
                        relief="solid", 
                        borderwidth=1,
                        font=("Segoe UI", 9),
                        padx=8, pady=4)
        label.pack()
    
    def on_leave(self, event):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


class LogHandler(logging.Handler):
    """Custom logging handler to redirect logs to GUI"""
    
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue
    
    def emit(self, record):
        log_entry = self.format(record)
        self.log_queue.put(log_entry)


class MediaScraperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Web Media Scraper")
        self.root.geometry("900x800")
        
        # Modern color scheme
        self.colors = {
            'bg_primary': '#2b2d31',      # Dark gray background
            'bg_secondary': '#36393f',     # Slightly lighter gray
            'bg_tertiary': '#40444b',      # Card/panel background
            'accent': '#5865f2',           # Discord blue accent
            'accent_hover': '#4752c4',     # Darker blue for hover
            'success': '#57f287',          # Green for success
            'warning': '#fee75c',          # Yellow for warnings
            'danger': '#ed4245',           # Red for errors
            'text_primary': '#ffffff',     # White text
            'text_secondary': '#b9bbbe',   # Light gray text
            'text_muted': '#72767d',       # Muted gray text
            'border': '#4f545c',           # Border color
        }
        
        # Configure root window
        self.root.configure(bg=self.colors['bg_primary'])
        
        # Configure modern ttk style
        self.setup_modern_style()
        
        # Threading and logging setup
        self.scraping_thread = None
        self.is_scraping = False
        self.log_queue = queue.Queue()
        
        # Setup logging
        self.setup_logging()
        
        # Create GUI
        self.create_widgets()
        
        # Start log monitor
        self.monitor_logs()
    
    def setup_modern_style(self):
        """Setup modern styling for ttk widgets"""
        style = ttk.Style()
        
        # Configure modern button style
        style.configure('Modern.TButton',
                       background=self.colors['accent'],
                       foreground=self.colors['text_primary'],
                       borderwidth=0,
                       focuscolor='none',
                       relief='flat',
                       padding=(20, 10))
        
        style.map('Modern.TButton',
                 background=[('active', self.colors['accent_hover']),
                           ('pressed', self.colors['accent_hover'])])
        
        # Success button style
        style.configure('Success.TButton',
                       background=self.colors['success'],
                       foreground=self.colors['bg_primary'],
                       borderwidth=0,
                       focuscolor='none',
                       relief='flat',
                       padding=(20, 10))
        
        # Danger button style
        style.configure('Danger.TButton',
                       background=self.colors['danger'],
                       foreground=self.colors['text_primary'],
                       borderwidth=0,
                       focuscolor='none',
                       relief='flat',
                       padding=(15, 8))
        
        # Configure modern entry style
        style.configure('Modern.TEntry',
                       fieldbackground=self.colors['bg_tertiary'],
                       foreground=self.colors['text_primary'],
                       borderwidth=1,
                       relief='solid',
                       insertcolor=self.colors['text_primary'])
        
        # Configure modern label style
        style.configure('Modern.TLabel',
                       background=self.colors['bg_primary'],
                       foreground=self.colors['text_primary'])
        
        style.configure('Heading.TLabel',
                       background=self.colors['bg_primary'],
                       foreground=self.colors['text_primary'],
                       font=('Segoe UI', 16, 'bold'))
        
        style.configure('Subheading.TLabel',
                       background=self.colors['bg_primary'],
                       foreground=self.colors['text_secondary'],
                       font=('Segoe UI', 9))
        
        # Configure modern frame style
        style.configure('Modern.TFrame',
                       background=self.colors['bg_primary'],
                       relief='flat')
        
        style.configure('Card.TFrame',
                       background=self.colors['bg_tertiary'],
                       relief='flat',
                       borderwidth=1)
        
        # Configure modern labelframe style
        style.configure('Modern.TLabelframe',
                       background=self.colors['bg_primary'],
                       foreground=self.colors['text_primary'],
                       borderwidth=1,
                       relief='solid')
        
        style.configure('Modern.TLabelframe.Label',
                       background=self.colors['bg_primary'],
                       foreground=self.colors['text_secondary'],
                       font=('Segoe UI', 10, 'bold'))
        
        # Configure modern checkbutton style
        style.configure('Modern.TCheckbutton',
                       background=self.colors['bg_primary'],
                       foreground=self.colors['text_primary'],
                       focuscolor='none')
        
        # Configure modern progressbar style
        style.configure('Modern.TProgressbar',
                       background=self.colors['accent'],
                       troughcolor=self.colors['bg_tertiary'],
                       borderwidth=0,
                       relief='flat')
    
    def setup_logging(self):
        """Setup logging to redirect to GUI"""
        # Create custom handler for GUI
        self.gui_handler = LogHandler(self.log_queue)
        self.gui_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        self.gui_handler.setFormatter(formatter)
        
        # Configure root logger
        logging.getLogger().setLevel(logging.INFO)
        logging.getLogger().addHandler(self.gui_handler)
    
    def create_widgets(self):
        """Create the main GUI widgets with modern styling"""
        # Create main canvas for scrolling
        self.main_canvas = tk.Canvas(self.root, bg=self.colors['bg_primary'], highlightthickness=0)
        self.main_canvas.pack(side='left', fill='both', expand=True)
        
        # Add global scrollbar for entire window
        global_scrollbar = tk.Scrollbar(self.root, orient='vertical', command=self.main_canvas.yview,
                                       bg=self.colors['bg_secondary'],
                                       troughcolor=self.colors['bg_primary'],
                                       activebackground=self.colors['accent'],
                                       highlightthickness=0,
                                       bd=1,
                                       width=16,
                                       elementborderwidth=1,
                                       relief='raised')
        global_scrollbar.pack(side='right', fill='y')
        self.main_canvas.configure(yscrollcommand=global_scrollbar.set)
        
        # Create scrollable frame inside canvas
        self.scrollable_frame = tk.Frame(self.main_canvas, bg=self.colors['bg_primary'])
        self.canvas_window = self.main_canvas.create_window((0, 0), window=self.scrollable_frame, anchor='nw')
        
        # Main container with padding inside the scrollable frame
        main_container = tk.Frame(self.scrollable_frame, bg=self.colors['bg_primary'])
        main_container.pack(fill='both', expand=True, padx=15, pady=(0, 15))  # Removed top padding
        
        # Configure grid weights
        main_container.columnconfigure(1, weight=1)
        main_container.rowconfigure(8, weight=1)  # Log area should expand (changed from row 9)
        
        # Modern title section
        title_frame = tk.Frame(main_container, bg=self.colors['bg_primary'])
        title_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))  # Reduced from 30 to 20
        
        title_label = tk.Label(title_frame, text="Web Media Scraper", 
                              font=('Segoe UI', 20, 'bold'),
                              fg=self.colors['text_primary'],
                              bg=self.colors['bg_primary'])
        title_label.pack(side=tk.LEFT)
        
        subtitle_label = tk.Label(title_frame, text="Professional media file discovery tool", 
                                 font=('Segoe UI', 10),
                                 fg=self.colors['text_secondary'],
                                 bg=self.colors['bg_primary'])
        subtitle_label.pack(side=tk.LEFT, padx=(15, 0))
        
        # Input section with cards
        self.create_input_section(main_container, 1)
        
        # Options section
        self.create_options_section(main_container, 5)
        
        # Control buttons
        self.create_control_section(main_container, 6)
        
        # Progress section
        self.create_progress_section(main_container, 7)
        
        # Log section
        self.create_log_section(main_container, 8)
        
        # Status section
        self.create_status_section(main_container, 9)  # Moved up from row 10
        
        # Configure canvas scrolling
        self.setup_canvas_scrolling()
    
    def setup_canvas_scrolling(self):
        """Setup canvas scrolling functionality"""
        # Update scroll region when frame changes
        def configure_scroll_region(event=None):
            self.main_canvas.configure(scrollregion=self.main_canvas.bbox('all'))
            
            # Make canvas window width match canvas width
            canvas_width = self.main_canvas.winfo_width()
            if canvas_width > 1:  # Only if canvas is properly sized
                self.main_canvas.itemconfig(self.canvas_window, width=canvas_width)
        
        self.scrollable_frame.bind('<Configure>', configure_scroll_region)
        self.main_canvas.bind('<Configure>', configure_scroll_region)
        
        # Bind mouse wheel scrolling
        def on_mousewheel(event):
            # Check if we're over the main canvas (not the log text widget)
            widget = event.widget
            if widget == self.main_canvas or widget in [self.scrollable_frame] or str(widget).startswith(str(self.scrollable_frame)):
                self.main_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        # Bind mouse wheel to canvas and all child widgets
        def bind_mousewheel(widget):
            widget.bind("<MouseWheel>", on_mousewheel)  # Windows/Mac
            widget.bind("<Button-4>", lambda e: self.main_canvas.yview_scroll(-1, "units"))  # Linux scroll up
            widget.bind("<Button-5>", lambda e: self.main_canvas.yview_scroll(1, "units"))   # Linux scroll down
            
            # Recursively bind to all children except log text (which has its own scrolling)
            for child in widget.winfo_children():
                if child != self.log_text:  # Don't interfere with log scrolling
                    bind_mousewheel(child)
        
        # Initial binding
        self.root.after(100, lambda: bind_mousewheel(self.root))
        
        # Update scroll region initially
        self.root.after(100, configure_scroll_region)
    
    def create_input_section(self, parent, start_row):
        """Create input fields with modern card styling"""
        # URL Input Card
        url_card = tk.Frame(parent, bg=self.colors['bg_tertiary'], relief='flat', bd=1)
        url_card.grid(row=start_row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        url_card.columnconfigure(1, weight=1)
        
        tk.Label(url_card, text="Starting URL", 
                font=('Segoe UI', 11, 'bold'),
                fg=self.colors['text_primary'],
                bg=self.colors['bg_tertiary']).grid(row=0, column=0, sticky=tk.W, padx=15, pady=(15, 5))
        
        self.url_var = tk.StringVar()
        url_entry = tk.Entry(url_card, textvariable=self.url_var,
                            font=('Segoe UI', 10),
                            bg=self.colors['bg_secondary'],
                            fg=self.colors['text_primary'],
                            insertbackground=self.colors['text_primary'],
                            relief='flat', bd=0)
        url_entry.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=15, pady=(0, 15))
        ToolTip(url_entry, "Enter the starting URL to begin scraping (e.g., https://example.com/page1)")
        
        # File Types Card
        types_card = tk.Frame(parent, bg=self.colors['bg_tertiary'], relief='flat', bd=1)
        types_card.grid(row=start_row+1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        types_card.columnconfigure(1, weight=1)
        
        tk.Label(types_card, text="File Types", 
                font=('Segoe UI', 11, 'bold'),
                fg=self.colors['text_primary'],
                bg=self.colors['bg_tertiary']).grid(row=0, column=0, sticky=tk.W, padx=15, pady=(15, 5))
        
        self.filetypes_var = tk.StringVar(value="mp4,webm,avi,mov")
        types_entry = tk.Entry(types_card, textvariable=self.filetypes_var,
                              font=('Segoe UI', 10),
                              bg=self.colors['bg_secondary'],
                              fg=self.colors['text_primary'],
                              insertbackground=self.colors['text_primary'],
                              relief='flat', bd=0)
        types_entry.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=15, pady=(0, 5))
        ToolTip(types_entry, "File extensions to search for, separated by commas")
        
        tk.Label(types_card, text="Comma-separated (e.g., mp4,webm,avi,mov)", 
                font=('Segoe UI', 9),
                fg=self.colors['text_muted'],
                bg=self.colors['bg_tertiary']).grid(row=2, column=0, sticky=tk.W, padx=15, pady=(0, 15))
        
        # Next Patterns Card  
        patterns_card = tk.Frame(parent, bg=self.colors['bg_tertiary'], relief='flat', bd=1)
        patterns_card.grid(row=start_row+2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        patterns_card.columnconfigure(1, weight=1)
        
        tk.Label(patterns_card, text="Next Page Patterns", 
                font=('Segoe UI', 11, 'bold'),
                fg=self.colors['text_primary'],
                bg=self.colors['bg_tertiary']).grid(row=0, column=0, sticky=tk.W, padx=15, pady=(15, 5))
        
        self.next_patterns_var = tk.StringVar(value="next,>>,→,continue,more")
        patterns_entry = tk.Entry(patterns_card, textvariable=self.next_patterns_var,
                                 font=('Segoe UI', 10),
                                 bg=self.colors['bg_secondary'],
                                 fg=self.colors['text_primary'],
                                 insertbackground=self.colors['text_primary'],
                                 relief='flat', bd=0)
        patterns_entry.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=15, pady=(0, 5))
        ToolTip(patterns_entry, "Text patterns that indicate 'next page' links")
        
        tk.Label(patterns_card, text="Text patterns to find pagination links", 
                font=('Segoe UI', 9),
                fg=self.colors['text_muted'],
                bg=self.colors['bg_tertiary']).grid(row=2, column=0, sticky=tk.W, padx=15, pady=(0, 15))
        
        # Output File Card
        output_card = tk.Frame(parent, bg=self.colors['bg_tertiary'], relief='flat', bd=1)
        output_card.grid(row=start_row+3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        output_card.columnconfigure(1, weight=1)
        
        tk.Label(output_card, text="Output File", 
                font=('Segoe UI', 11, 'bold'),
                fg=self.colors['text_primary'],
                bg=self.colors['bg_tertiary']).grid(row=0, column=0, sticky=tk.W, padx=15, pady=(15, 5))
        
        output_frame = tk.Frame(output_card, bg=self.colors['bg_tertiary'])
        output_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=15, pady=(0, 15))
        output_frame.columnconfigure(0, weight=1)
        
        self.output_var = tk.StringVar(value="scraped_links.txt")
        output_entry = tk.Entry(output_frame, textvariable=self.output_var,
                               font=('Segoe UI', 10),
                               bg=self.colors['bg_secondary'],
                               fg=self.colors['text_primary'],
                               insertbackground=self.colors['text_primary'],
                               relief='flat', bd=0)
        output_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        browse_btn = tk.Button(output_frame, text="Browse", command=self.browse_output_file,
                              font=('Segoe UI', 9),
                              bg=self.colors['accent'],
                              fg=self.colors['text_primary'],
                              relief='flat', bd=0,
                              padx=15, pady=8,
                              cursor='hand2')
        browse_btn.grid(row=0, column=1)
        
        # Add hover effects to browse button
        browse_btn.bind("<Enter>", lambda e: browse_btn.config(bg=self.colors['accent_hover']))
        browse_btn.bind("<Leave>", lambda e: browse_btn.config(bg=self.colors['accent']))
    
    def create_options_section(self, parent, row):
        """Create options section with modern styling"""
        options_card = tk.Frame(parent, bg=self.colors['bg_tertiary'], relief='flat', bd=1)
        options_card.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))
        
        tk.Label(options_card, text="Options", 
                font=('Segoe UI', 11, 'bold'),
                fg=self.colors['text_primary'],
                bg=self.colors['bg_tertiary']).grid(row=0, column=0, sticky=tk.W, padx=15, pady=(15, 10))
        
        # CAPTCHA checkbox with modern styling
        self.captcha_var = tk.BooleanVar()
        captcha_check = tk.Checkbutton(options_card, text="CAPTCHA Mode (opens visible browser)", 
                                      variable=self.captcha_var,
                                      font=('Segoe UI', 10),
                                      fg=self.colors['text_primary'],
                                      bg=self.colors['bg_tertiary'],
                                      selectcolor=self.colors['bg_secondary'],
                                      activebackground=self.colors['bg_tertiary'],
                                      activeforeground=self.colors['text_primary'],
                                      relief='flat')
        captcha_check.grid(row=1, column=0, columnspan=2, sticky=tk.W, padx=15, pady=(0, 15))
        ToolTip(captcha_check, "Enable to open a visible browser window for manual CAPTCHA solving")
    
    def create_control_section(self, parent, row):
        """Create control buttons with modern styling"""
        control_frame = tk.Frame(parent, bg=self.colors['bg_primary'])
        control_frame.grid(row=row, column=0, columnspan=2, pady=10)  # Reduced from 20 to 10
        
        self.start_btn = tk.Button(control_frame, text="Start Scraping", 
                                  command=self.start_scraping,
                                  font=('Segoe UI', 11, 'bold'),
                                  bg=self.colors['success'],
                                  fg=self.colors['bg_primary'],
                                  relief='flat', bd=0,
                                  padx=25, pady=8,  # Reduced from 30,12 to 25,8
                                  cursor='hand2')
        self.start_btn.pack(side=tk.LEFT, padx=(0, 8))  # Reduced from 10 to 8
        
        # Add hover effects
        self.start_btn.bind("<Enter>", lambda e: self.start_btn.config(bg='#4CAF50'))
        self.start_btn.bind("<Leave>", lambda e: self.start_btn.config(bg=self.colors['success']))
        
        self.stop_btn = tk.Button(control_frame, text="Stop", 
                                 command=self.stop_scraping, 
                                 state='disabled',
                                 font=('Segoe UI', 11, 'bold'),
                                 bg=self.colors['danger'],
                                 fg=self.colors['text_primary'],
                                 relief='flat', bd=0,
                                 padx=18, pady=8,  # Reduced from 20,12 to 18,8
                                 cursor='hand2')
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 8))  # Reduced from 10 to 8
        
        # Add hover effects
        self.stop_btn.bind("<Enter>", lambda e: self.stop_btn.config(bg='#F44336') if self.stop_btn['state'] != 'disabled' else None)
        self.stop_btn.bind("<Leave>", lambda e: self.stop_btn.config(bg=self.colors['danger']) if self.stop_btn['state'] != 'disabled' else None)
        
        self.clear_btn = tk.Button(control_frame, text="Clear Log", 
                                  command=self.clear_log,
                                  font=('Segoe UI', 10),
                                  bg=self.colors['bg_tertiary'],
                                  fg=self.colors['text_primary'],
                                  relief='flat', bd=0,
                                  padx=12, pady=6,  # Reduced from 15,10 to 12,6
                                  cursor='hand2')
        self.clear_btn.pack(side=tk.LEFT)
        
        # Add hover effects
        self.clear_btn.bind("<Enter>", lambda e: self.clear_btn.config(bg=self.colors['bg_secondary']))
        self.clear_btn.bind("<Leave>", lambda e: self.clear_btn.config(bg=self.colors['bg_tertiary']))
    
    def create_progress_section(self, parent, row):
        """Create progress section with modern styling"""
        progress_frame = tk.Frame(parent, bg=self.colors['bg_primary'])
        progress_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        progress_frame.columnconfigure(0, weight=1)
        
        # Create a custom progress bar using a frame and canvas
        self.progress_container = tk.Frame(progress_frame, bg=self.colors['bg_tertiary'], height=8)
        self.progress_container.grid(row=0, column=0, sticky=(tk.W, tk.E))
        self.progress_container.columnconfigure(0, weight=1)
        
        self.progress_canvas = tk.Canvas(self.progress_container, height=6, 
                                        bg=self.colors['bg_tertiary'], 
                                        highlightthickness=0)
        self.progress_canvas.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=2, pady=1)
        
        # Animation variables
        self.progress_running = False
        self.progress_position = 0
    
    def start_progress_animation(self):
        """Start custom progress bar animation"""
        self.progress_running = True
        self.animate_progress()
    
    def stop_progress_animation(self):
        """Stop custom progress bar animation"""
        self.progress_running = False
        self.progress_canvas.delete("all")
    
    def animate_progress(self):
        """Animate the custom progress bar"""
        if not self.progress_running:
            return
        
        # Clear previous drawing
        self.progress_canvas.delete("all")
        
        # Get canvas dimensions
        width = self.progress_canvas.winfo_width()
        height = self.progress_canvas.winfo_height()
        
        if width > 1:  # Only draw if canvas is properly sized
            # Create moving gradient effect
            bar_width = width // 3
            x = (self.progress_position % (width + bar_width)) - bar_width
            
            # Draw the moving bar
            self.progress_canvas.create_rectangle(
                x, 0, x + bar_width, height,
                fill=self.colors['accent'], outline=""
            )
            
            self.progress_position += 2
        
        # Schedule next frame
        self.root.after(50, self.animate_progress)
    
    def create_log_section(self, parent, row):
        """Create log section with modern styling"""
        log_card = tk.Frame(parent, bg=self.colors['bg_tertiary'], relief='flat', bd=1)
        log_card.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 15))
        log_card.columnconfigure(0, weight=1)
        log_card.rowconfigure(1, weight=1)
        
        tk.Label(log_card, text="Activity Log", 
                font=('Segoe UI', 11, 'bold'),
                fg=self.colors['text_primary'],
                bg=self.colors['bg_tertiary']).grid(row=0, column=0, sticky=tk.W, padx=15, pady=(15, 10))
        
        # Custom text widget with modern styling - reduced height
        self.log_text = tk.Text(log_card, height=8, wrap=tk.WORD,  # Reduced from 12 to 8
                               font=('Consolas', 9),
                               bg=self.colors['bg_secondary'],
                               fg=self.colors['text_primary'],
                               insertbackground=self.colors['text_primary'],
                               relief='flat', bd=0,
                               selectbackground=self.colors['accent'],
                               selectforeground=self.colors['text_primary'])
        self.log_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(15, 5), pady=(0, 15))
        
        # Modern styled scrollbar for log - always visible
        scrollbar = tk.Scrollbar(log_card, command=self.log_text.yview,
                                orient='vertical',
                                bg=self.colors['bg_secondary'],      # Darker background
                                troughcolor=self.colors['bg_primary'], # Even darker trough
                                activebackground=self.colors['accent'], # Bright when active
                                highlightthickness=0,
                                bd=1,                                # Add border
                                width=16,                            # Make wider for visibility
                                elementborderwidth=1,
                                relief='raised',                     # Make it stand out
                                activerelief='raised')
        
        # Override system colors to ensure visibility
        scrollbar.configure(
            bg=self.colors['bg_secondary'],           # Scrollbar background
            troughcolor=self.colors['bg_primary'],    # Track (trough) color  
            activebackground=self.colors['accent'],   # Color when clicked/active
            highlightbackground=self.colors['bg_tertiary'], # Highlight background
            highlightcolor=self.colors['accent'],     # Highlight color
            jump=0,                                   # Don't jump, smooth scroll
            repeatdelay=300,                          # Repeat delay for holding
            repeatinterval=100                        # Repeat interval
        )
        
        scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S), pady=(0, 15), padx=(0, 15))
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # Add initial welcome message to show scrollbar
        welcome_msg = ("Welcome to Web Media Scraper!\n"
                      "Enter a starting URL to begin\n" 
                      "Configure file types to search for\n"
                      "Set pagination patterns\n"
                      "Click 'Start Scraping' when ready\n"
                      "Scroll here to see activity logs...\n")
        self.log_text.insert(tk.END, welcome_msg)
        self.log_text.see(tk.END)
    
    def create_status_section(self, parent, row):
        """Create status section with modern styling"""
        status_card = tk.Frame(parent, bg=self.colors['bg_tertiary'], relief='flat', bd=1)
        status_card.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E))
        status_card.columnconfigure(1, weight=1)
        
        self.status_var = tk.StringVar(value="Ready")
        status_label = tk.Label(status_card, textvariable=self.status_var,
                               font=('Segoe UI', 10),
                               fg=self.colors['text_primary'],
                               bg=self.colors['bg_tertiary'])
        status_label.grid(row=0, column=0, sticky=tk.W, padx=15, pady=10)
        
        # Results summary
        self.results_var = tk.StringVar(value="")
        results_label = tk.Label(status_card, textvariable=self.results_var, 
                                font=('Segoe UI', 10, 'bold'),
                                fg=self.colors['success'],
                                bg=self.colors['bg_tertiary'])
        results_label.grid(row=0, column=1, sticky=tk.E, padx=15, pady=10)
    
    def browse_output_file(self):
        """Open file dialog to select output file"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=self.output_var.get()
        )
        if filename:
            self.output_var.set(filename)
    
    def monitor_logs(self):
        """Monitor log queue and update GUI"""
        try:
            while True:
                log_entry = self.log_queue.get_nowait()
                self.log_text.insert(tk.END, log_entry + "\n")
                self.log_text.see(tk.END)
        except queue.Empty:
            pass
        
        self.root.after(100, self.monitor_logs)
    
    def clear_log(self):
        """Clear the log text area"""
        self.log_text.delete(1.0, tk.END)
    
    def validate_inputs(self):
        """Validate user inputs"""
        if not self.url_var.get().strip():
            messagebox.showerror("Error", "Please enter a starting URL")
            return False
        
        if not self.filetypes_var.get().strip():
            messagebox.showerror("Error", "Please enter at least one file type")
            return False
        
        return True
    
    def start_scraping(self):
        """Start the scraping process in a separate thread"""
        if not self.validate_inputs():
            return
        
        if self.is_scraping:
            messagebox.showwarning("Warning", "Scraping is already in progress")
            return
        
        # Update UI state
        self.is_scraping = True
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.start_progress_animation()
        self.status_var.set("Scraping in progress...")
        
        # Start scraping thread
        self.scraping_thread = threading.Thread(target=self.scrape_media, daemon=True)
        self.scraping_thread.start()
    
    def stop_scraping(self):
        """Stop the scraping process"""
        self.is_scraping = False
        self.status_var.set("Stopping...")
        logging.info("Stopping scraper...")
        
        # Force stop by updating UI immediately
        self.root.update_idletasks()
    
    def scraping_finished(self, success=True):
        """Called when scraping is finished"""
        self.is_scraping = False
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.stop_progress_animation()
        
        if success:
            self.status_var.set("Scraping completed successfully")
        else:
            self.status_var.set("Scraping stopped or failed")
    
    def setup_selenium_driver(self, captcha_mode=False):
        """Setup Chrome WebDriver for JavaScript rendering"""
        try:
            chrome_options = Options()
            if not captcha_mode:
                chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36")
            
            # Try different Chrome binary locations
            chrome_paths = [
                "/usr/bin/google-chrome-stable",
                "/usr/bin/google-chrome",
                "/usr/bin/chromium-browser",
                "/usr/bin/chromium"
            ]
            
            for path in chrome_paths:
                if os.path.exists(path):
                    chrome_options.binary_location = path
                    break
            
            # Reduce timeouts for better responsiveness
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_page_load_timeout(10)  # Reduced from 15
            return driver
        except Exception as e:
            error_msg = f"Failed to setup Chrome driver: {e}\n\nPlease ensure Chrome/Chromium is installed and chromedriver is in PATH."
            logging.error(error_msg)
            self.root.after(0, lambda: messagebox.showerror("Driver Error", error_msg))
            return None
    
    def get_media_links(self, driver, file_extensions):
        """Find media links using Selenium with configurable file types"""
        media_links = []
        
        # Check if we should stop before starting
        if not self.is_scraping:
            return []
        
        try:
            # Wait for page to load with shorter timeout
            WebDriverWait(driver, 2).until(  # Reduced from 3
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Check again after waiting
            if not self.is_scraping:
                return []
            
            WebDriverWait(driver, 3).until(  # Reduced from 5
                lambda d: len(d.page_source) > 10000 or  
                d.find_elements(By.XPATH, "//video | //img | //a | //*[contains(@class, 'post')]")
            )
        except Exception as e:
            logging.warning(f"Content loading timeout: {e}")
            # Still continue to scrape what we can
        
        # Final check before processing
        if not self.is_scraping:
            return []
        
        page_source = driver.page_source
        
        # Create regex patterns for each file type
        for ext in file_extensions:
            patterns = [
                rf'https?://[^\s"\'<>]*\.{ext}[^\s"\'<>]*',
                rf'//[^\s"\'<>]*\.{ext}[^\s"\'<>]*',
                rf'/[^\s"\'<>]*\.{ext}[^\s"\'<>]*',
                rf'[^\s"\'<>]*\.{ext}[^\s"\'<>]*',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, page_source, re.IGNORECASE)
                media_links.extend(matches)
        
        # Check DOM elements
        try:
            ext_xpath = " or ".join([f"contains(., '.{ext}')" for ext in file_extensions])
            selectors = [
                f"//*[@href[{ext_xpath}]]",
                f"//*[@src[{ext_xpath}]]",
                f"//*[@data-src[{ext_xpath}]]",
                f"//*[@data-url[{ext_xpath}]]",
                f"//*[@data-video[{ext_xpath}]]",
                "//video[@src]",
                "//source[@src]",
            ]
            
            for selector in selectors:
                try:
                    elements = driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        for attr in ['href', 'src', 'data-src', 'data-url', 'data-video']:
                            try:
                                value = element.get_attribute(attr)
                                if value and any(f'.{ext}' in value.lower() for ext in file_extensions):
                                    media_links.append(value)
                            except:
                                continue
                except:
                    continue
        except Exception as e:
            logging.debug(f"Error getting DOM elements: {e}")
        
        # Clean and deduplicate links
        unique_links = []
        for link in set(media_links):
            link = link.strip()
            if link and any(f'.{ext}' in link.lower() for ext in file_extensions):
                # Convert relative URLs to absolute
                if link.startswith('//'):
                    link = 'https:' + link
                elif link.startswith('/') and not link.startswith('//'):
                    base_url = driver.current_url.split('://', 1)[1].split('/', 1)[0]
                    link = f'https://{base_url}' + link
                unique_links.append(link)
        
        return list(set(unique_links))
    
    def find_next_page(self, driver, next_patterns):
        """Find next page using configurable patterns"""
        try:
            # Check if we should stop
            if not self.is_scraping:
                return None
                
            wait = WebDriverWait(driver, 2)
            
            # Try each pattern
            for pattern in next_patterns:
                # Check if we should stop during pattern iteration
                if not self.is_scraping:
                    return None
                    
                selectors = [
                    f"a[class*='{pattern}']",
                    f"a[rel='{pattern}']",
                    f"a[title*='{pattern}']",
                    f"a:contains('{pattern}')",
                    f"//*[contains(text(), '{pattern}')]/ancestor-or-self::a",
                ]
                
                for selector in selectors:
                    # Check if we should stop during selector iteration
                    if not self.is_scraping:
                        return None
                        
                    try:
                        if selector.startswith("//"):
                            next_link = wait.until(
                                EC.presence_of_element_located((By.XPATH, selector))
                            )
                        else:
                            next_link = wait.until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                            )
                        
                        href = next_link.get_attribute("href")
                        if href:
                            return href
                    except:
                        continue
        except:
            pass
        
        return None
    
    def save_media_links_to_file(self, media_links, filename):
        """Save media links to file"""
        try:
            with open(filename, "a") as f:
                for link in sorted(media_links):
                    f.write(link + "\n")
            logging.info(f"Appended {len(media_links)} links to {filename}")
            return True
        except Exception as e:
            logging.error(f"Failed to save links to file: {e}")
            return False
    
    def scrape_media(self):
        """Main scraping function"""
        try:
            # Get parameters
            url = self.url_var.get().strip()
            file_types = [ft.strip().lower() for ft in self.filetypes_var.get().split(',') if ft.strip()]
            next_patterns = [p.strip().lower() for p in self.next_patterns_var.get().split(',') if p.strip()]
            output_file = self.output_var.get().strip()
            captcha_mode = self.captcha_var.get()
            
            logging.info("Starting Web Media Scraper")
            logging.info(f"Target URL: {url}")
            logging.info(f"Output file: {output_file}")
            logging.info(f"File types: {', '.join(file_types)}")
            logging.info(f"Next patterns: {', '.join(next_patterns)}")
            
            # Setup driver
            driver = self.setup_selenium_driver(captcha_mode)
            if not driver:
                logging.error("Failed to setup Selenium driver - exiting")
                self.scraping_finished(False)
                return
            
            try:
                collected_media = set()
                page_url = url
                page_count = 0
                
                # CAPTCHA handling
                if captcha_mode:
                    logging.info("CAPTCHA MODE: Opening browser for manual intervention...")
                    driver.get(page_url)
                    
                    # Create a dialog for CAPTCHA mode
                    def show_captcha_dialog():
                        result = messagebox.askokcancel(
                            "CAPTCHA Mode", 
                            "Browser opened for CAPTCHA solving.\n\n"
                            "Please:\n"
                            "1. Solve any CAPTCHAs that appear\n"
                            "2. Complete verification steps\n"
                            "3. Click OK when ready to continue\n"
                            "4. Click Cancel to abort scraping"
                        )
                        return result
                    
                    # Run dialog in main thread
                    continue_scraping = True
                    dialog_result = None
                    
                    def run_dialog():
                        nonlocal dialog_result
                        dialog_result = show_captcha_dialog()
                    
                    self.root.after(0, run_dialog)
                    
                    # Wait for dialog result
                    while dialog_result is None and self.is_scraping:
                        time.sleep(0.1)
                    
                    if not dialog_result or not self.is_scraping:
                        logging.info("CAPTCHA solving cancelled by user")
                        self.scraping_finished(False)
                        return
                
                pages_without_media = 0
                
                while page_url and self.is_scraping:
                    page_count += 1
                    logging.info(f"Processing page {page_count}: {page_url}")
                    
                    # Check if we should stop before processing this page
                    if not self.is_scraping:
                        break
                    
                    try:
                        if not captcha_mode or page_count > 1:
                            # Check again before navigating to new page
                            if not self.is_scraping:
                                break
                            driver.get(page_url)
                        
                        # Check again after page load
                        if not self.is_scraping:
                            break
                            
                        page_media = self.get_media_links(driver, file_types)
                        
                        if page_media:
                            new_links = set(page_media) - collected_media
                            collected_media.update(page_media)
                            pages_without_media = 0
                            
                            if new_links:
                                logging.info(f"Page {page_count}: FOUND {len(new_links)} new files! (Total: {len(collected_media)})")
                                for link in list(new_links)[:5]:  # Show first 5
                                    logging.info(f"  {link}")
                                if len(new_links) > 5:
                                    logging.info(f"  ... and {len(new_links) - 5} more")
                                
                                self.save_media_links_to_file(new_links, output_file)
                            else:
                                logging.info(f"Page {page_count}: No new files (all duplicates)")
                        else:
                            pages_without_media += 1
                            if pages_without_media <= 5:
                                logging.info(f"Page {page_count}: No media files found")
                        
                        # Find next page
                        if not self.is_scraping:
                            break
                        page_url = self.find_next_page(driver, next_patterns)
                        if page_url:
                            # Responsive sleep - check every 0.1 seconds
                            sleep_time = 0.1 if pages_without_media > 0 else 0.3
                            sleep_steps = int(sleep_time / 0.1)
                            for _ in range(sleep_steps):
                                if not self.is_scraping:
                                    break
                                time.sleep(0.1)
                        else:
                            logging.info("No more pages found")
                            break
                    
                    except Exception as e:
                        logging.error(f"Error on page {page_count}: {e}")
                        break
                
                # Final summary
                if collected_media:
                    logging.info(f"SUCCESS! Found {len(collected_media)} media links total")
                    logging.info(f"Saved to: {output_file}")
                    self.root.after(0, lambda: self.results_var.set(f"Found {len(collected_media)} media files"))
                else:
                    logging.warning("No media links found")
                    self.root.after(0, lambda: self.results_var.set("No media files found"))
                
                self.scraping_finished(True)
                
            finally:
                driver.quit()
                logging.info("Browser closed")
        
        except Exception as e:
            logging.error(f"Fatal error during scraping: {e}")
            self.scraping_finished(False)


def main():
    root = tk.Tk()
    app = MediaScraperGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
