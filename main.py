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
    """Simple tooltip class for GUI elements"""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
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
                        background="lightyellow", relief="solid", borderwidth=1,
                        font=("Arial", 8))
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
        self.root.title("Web Media Scraper - Portfolio Project")
        self.root.geometry("800x700")
        
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        
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
        """Create the main GUI widgets"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Web Media Scraper", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # URL Input
        ttk.Label(main_frame, text="Starting URL:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.url_var = tk.StringVar()
        url_entry = ttk.Entry(main_frame, textvariable=self.url_var, width=60)
        url_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        ToolTip(url_entry, "Enter the starting URL to begin scraping (e.g., https://example.com/page1)")
        
        # File Types Input
        ttk.Label(main_frame, text="File Types:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.filetypes_var = tk.StringVar(value="mp4,webm,avi,mov")
        filetypes_entry = ttk.Entry(main_frame, textvariable=self.filetypes_var, width=60)
        filetypes_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        ToolTip(filetypes_entry, "File extensions to search for, separated by commas")
        ttk.Label(main_frame, text="(comma-separated, e.g., mp4,webm,avi)", 
                 font=('Arial', 8)).grid(row=3, column=1, sticky=tk.W, padx=(10, 0))
        
        # Next Link Patterns
        ttk.Label(main_frame, text="Next Link Patterns:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.next_patterns_var = tk.StringVar(value="next,>>,→,continue,more")
        next_patterns_entry = ttk.Entry(main_frame, textvariable=self.next_patterns_var, width=60)
        next_patterns_entry.grid(row=4, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        ToolTip(next_patterns_entry, "Text patterns that indicate 'next page' links")
        ttk.Label(main_frame, text="(comma-separated text patterns to find next page)", 
                 font=('Arial', 8)).grid(row=5, column=1, sticky=tk.W, padx=(10, 0))
        
        # Output File
        ttk.Label(main_frame, text="Output File:").grid(row=6, column=0, sticky=tk.W, pady=5)
        output_frame = ttk.Frame(main_frame)
        output_frame.grid(row=6, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        output_frame.columnconfigure(0, weight=1)
        
        self.output_var = tk.StringVar(value="scraped_links.txt")
        output_entry = ttk.Entry(output_frame, textvariable=self.output_var)
        output_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        browse_btn = ttk.Button(output_frame, text="Browse", command=self.browse_output_file)
        browse_btn.grid(row=0, column=1)
        
        # Options frame
        options_frame = ttk.LabelFrame(main_frame, text="Options", padding="10")
        options_frame.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        # CAPTCHA mode checkbox
        self.captcha_var = tk.BooleanVar()
        captcha_check = ttk.Checkbutton(options_frame, text="CAPTCHA Mode (opens visible browser)", 
                                       variable=self.captcha_var)
        captcha_check.grid(row=0, column=0, sticky=tk.W)
        ToolTip(captcha_check, "Enable to open a visible browser window for manual CAPTCHA solving")
        
        # Max pages
        ttk.Label(options_frame, text="Max Pages (0 = unlimited):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.max_pages_var = tk.StringVar(value="50")
        max_pages_entry = ttk.Entry(options_frame, textvariable=self.max_pages_var, width=10)
        max_pages_entry.grid(row=1, column=1, sticky=tk.W, padx=(10, 0))
        ToolTip(max_pages_entry, "Maximum number of pages to scrape (0 for unlimited)")
        
        # Control buttons
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=8, column=0, columnspan=2, pady=20)
        
        self.start_btn = ttk.Button(control_frame, text="Start Scraping", 
                                   command=self.start_scraping, style='Accent.TButton')
        self.start_btn.grid(row=0, column=0, padx=5)
        
        self.stop_btn = ttk.Button(control_frame, text="Stop", 
                                  command=self.stop_scraping, state='disabled')
        self.stop_btn.grid(row=0, column=1, padx=5)
        
        self.clear_btn = ttk.Button(control_frame, text="Clear Log", 
                                   command=self.clear_log)
        self.clear_btn.grid(row=0, column=2, padx=5)
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=9, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        # Log output
        log_frame = ttk.LabelFrame(main_frame, text="Log Output", padding="5")
        log_frame.grid(row=10, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(10, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Status bar and results
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=11, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        status_frame.columnconfigure(1, weight=1)
        
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(status_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        # Results summary
        self.results_var = tk.StringVar(value="")
        results_label = ttk.Label(status_frame, textvariable=self.results_var, font=('Arial', 9, 'bold'))
        results_label.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(2, 0))
    
    def browse_output_file(self):
        """Open file dialog to select output file"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialvalue=self.output_var.get()
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
        
        try:
            max_pages = int(self.max_pages_var.get()) if self.max_pages_var.get() else 0
            if max_pages < 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Error", "Max pages must be a positive number or 0")
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
        self.progress.start()
        self.status_var.set("Scraping in progress...")
        
        # Start scraping thread
        self.scraping_thread = threading.Thread(target=self.scrape_media, daemon=True)
        self.scraping_thread.start()
    
    def stop_scraping(self):
        """Stop the scraping process"""
        self.is_scraping = False
        self.status_var.set("Stopping...")
        logging.info("🛑 Stopping scraper...")
    
    def scraping_finished(self, success=True):
        """Called when scraping is finished"""
        self.is_scraping = False
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.progress.stop()
        
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
            
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_page_load_timeout(15)
            return driver
        except Exception as e:
            error_msg = f"Failed to setup Chrome driver: {e}\n\nPlease ensure Chrome/Chromium is installed and chromedriver is in PATH."
            logging.error(error_msg)
            self.root.after(0, lambda: messagebox.showerror("Driver Error", error_msg))
            return None
    
    def get_media_links(self, driver, file_extensions):
        """Find media links using Selenium with configurable file types"""
        media_links = []
        
        try:
            # Wait for page to load
            WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            WebDriverWait(driver, 5).until(
                lambda d: len(d.page_source) > 10000 or  
                d.find_elements(By.XPATH, "//video | //img | //a | //*[contains(@class, 'post')]")
            )
        except Exception as e:
            logging.warning(f"Content loading timeout: {e}")
        
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
            wait = WebDriverWait(driver, 2)
            
            # Try each pattern
            for pattern in next_patterns:
                selectors = [
                    f"a[class*='{pattern}']",
                    f"a[rel='{pattern}']",
                    f"a[title*='{pattern}']",
                    f"a:contains('{pattern}')",
                    f"//*[contains(text(), '{pattern}')]/ancestor-or-self::a",
                ]
                
                for selector in selectors:
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
            logging.info(f"💾 Appended {len(media_links)} links to {filename}")
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
            max_pages = int(self.max_pages_var.get()) if self.max_pages_var.get() else 0
            
            logging.info("🚀 Starting Web Media Scraper")
            logging.info(f"🎯 Target URL: {url}")
            logging.info(f"📁 Output file: {output_file}")
            logging.info(f"🎬 File types: {', '.join(file_types)}")
            logging.info(f"🔗 Next patterns: {', '.join(next_patterns)}")
            
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
                    logging.info("🧩 CAPTCHA MODE: Opening browser for manual intervention...")
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
                    if max_pages > 0 and page_count >= max_pages:
                        logging.info(f"🏁 Reached maximum pages limit ({max_pages})")
                        break
                    
                    page_count += 1
                    logging.info(f"Processing page {page_count}: {page_url}")
                    
                    try:
                        if not captcha_mode or page_count > 1:
                            driver.get(page_url)
                        
                        page_media = self.get_media_links(driver, file_types)
                        
                        if page_media:
                            new_links = set(page_media) - collected_media
                            collected_media.update(page_media)
                            pages_without_media = 0
                            
                            if new_links:
                                logging.info(f"🎉 Page {page_count}: FOUND {len(new_links)} new files! (Total: {len(collected_media)})")
                                for link in list(new_links)[:5]:  # Show first 5
                                    logging.info(f"  📹 {link}")
                                if len(new_links) > 5:
                                    logging.info(f"  ... and {len(new_links) - 5} more")
                                
                                self.save_media_links_to_file(new_links, output_file)
                            else:
                                logging.info(f"⚪ Page {page_count}: No new files (all duplicates)")
                        else:
                            pages_without_media += 1
                            if pages_without_media <= 5:
                                logging.info(f"⚪ Page {page_count}: No media files found")
                        
                        # Find next page
                        page_url = self.find_next_page(driver, next_patterns)
                        if page_url:
                            time.sleep(0.1 if pages_without_media > 0 else 0.3)
                        else:
                            logging.info("✅ No more pages found")
                            break
                    
                    except Exception as e:
                        logging.error(f"❌ Error on page {page_count}: {e}")
                        break
                
                # Final summary
                if collected_media:
                    logging.info(f"🎊 SUCCESS! Found {len(collected_media)} media links total")
                    logging.info(f"📁 Saved to: {output_file}")
                    self.root.after(0, lambda: self.results_var.set(f"✅ Found {len(collected_media)} media files"))
                else:
                    logging.warning("⚠️  No media links found")
                    self.root.after(0, lambda: self.results_var.set("⚠️ No media files found"))
                
                self.scraping_finished(True)
                
            finally:
                driver.quit()
                logging.info("🔒 Browser closed")
        
        except Exception as e:
            logging.error(f"Fatal error during scraping: {e}")
            self.scraping_finished(False)


def main():
    root = tk.Tk()
    app = MediaScraperGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
