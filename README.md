# Smart Media Finder

Python GUI application for scraping media links using Selenium. Features customized file type filtering, pagination support, and CAPTCHA handling.

## How to use

### Setup

1. Clone the repository and navigate to the folder.
2. Set up a virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Install the Chrome browser. This is required for Selenium.

### Run the program

Run the application:

```bash
python main.py
```

1. Enter the starting URL.
2. Configure file types and next-page patterns. Defaults are provided.
3. Enable CAPTCHA mode if needed.
4. Click "Start Scraping" and monitor progress.

### Requirements

- Python 3.7+
- Chrome or Chromium browser
- Dependencies listed in `requirements.txt`

## How it works

Smart Media Finder uses Selenium to control a Chrome browser and scrape pages. It runs multi-threaded, so the interface stays responsive during a scrape. It follows pagination by matching configurable "Next"-button patterns, to move through multiple pages. When CAPTCHA mode is enabled, the program pauses so a CAPTCHA can be solved manually.

## License

This project uses the GPL-3.0 license. See the [LICENSE.md](LICENSE.md) file for details.