# Web Media Scraper

A GUI application for scraping media files from websites with customizable parameters.

## Features

- **Easy-to-use GUI** with real-time log output
- **Customizable file types** (mp4, webm, avi, mov, etc.)
- **Pagination support** with configurable next-page patterns (_automatically follows "Next" buttons to scrape multiple pages_)
- **CAPTCHA handling** for sites requiring manual intervention
- **Multi-threaded** to keep UI responsive during scraping

## Installation

1. Clone the repository and navigate to the folder
2. Set up virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Install Chrome browser (required for Selenium)

## Usage

Run the application:

```bash
python main.py
```

1. Enter the starting URL
2. Configure file types and next-page patterns (defaults provided)
3. Enable CAPTCHA mode if needed
4. Click "Start Scraping" and monitor progress

## Requirements

- Python 3.7+
- Chrome/Chromium browser
- Dependencies listed in `requirements.txt`

## License

This project is licensed under the [GPL-3.0](LICENSE.md)
GNU General Public License - see the [LICENSE.md](LICENSE.md) file for
details.
