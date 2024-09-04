# QMUL-TimeTable-Scraper

**QMUL-TimeTable-Scraper** is a Python-based web scraper built using FastAPI and Selenium to generate a personal timetable from Queen Mary University of London's (QMUL) online timetable system. This project provides a web interface where users can input their Student ID (SID) and receive a downloadable `.ics` calendar file, which can be easily imported into calendar applications like Google Calendar, Outlook, and more.

## Features

- **Web Scraping**: Uses Selenium to scrape the QMUL timetable website for personalized schedule data.
- **ICS File Generation**: Automatically converts timetable data into a `.ics` calendar file that can be imported into calendar apps.
- **Static Form Interface**: A simple HTML form served via FastAPI to allow users to input their Student ID in a more user-friendly way.
- **Headless Browser**: Runs the scraping process in the background without opening a browser window, making it more efficient and lightweight.
- **FastAPI**: API backend to handle the web requests and serve the static assets.
- **BeautifulSoup**: For parsing HTML content and extracting relevant timetable data.

## Prerequisites

To run this project locally, you will need the following installed:

- Python 3.9 or higher
- Docker (for running the Browserless Selenium server)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/QMUL-TimeTable-Scraper.git
   cd QMUL-TimeTable-Scraper
   ```

2. Install the Python dependencies using pip (Optional - if not using the main docker image):
   ```bash
   pip install -r requirements.txt
   ```

3. Set up a Selenium server using Docker (this project uses a Browserless instance):
   ```bash
   docker pull browserless/chrome
   docker run -d -p 3000:3000 browserless/chrome
   ```
   
4. Build the main Docker image and run it:
   ```bash
   docker build -t timetable-scraper .
   docker run -d -p 8000:8000 timetable-scraper
   ```

5. Access the web interface at `http://localhost:8000/` in your browser.

## Usage

1. Navigate to the homepage at `http://localhost:8000/`.
2. Enter your **Student ID (SID)** into the form provided and submit the form.
3. The scraper will retrieve your timetable and generate an `.ics` calendar file.
4. The `.ics` file will be downloaded automatically to your system, ready to import into your preferred calendar application.

## API Endpoints

- **`GET /`**: Serves the static HTML form for SID input.
- **`POST /generate-ics`**: Accepts the Student ID via form data and returns a downloadable `.ics` file.

## File Structure

```bash
QMUL-TimeTable-Scraper/
│
├── Dockerfile         # Dockerfile to containerize the FastAPI app
├── main.py            # Main FastAPI app with scraping and ICS generation logic
├── static/            # Static files (HTML, CSS, JavaScript)
│   ├── index.html     # HTML form for SID input
│   ├── styles.css     # Custom CSS for form styling
│   └── favicon.ico    # Favicon for the app
├── requirements.txt   # Python dependencies
└── README.md          # Project documentation
```

## How It Works

1. **Selenium Web Scraper**:
   - A headless Chrome browser (managed by Selenium) is used to navigate the [offical QMUL timetable website](https://timetables.qmul.ac.uk/default.aspx).
   - The student’s ID is submitted via a form, and the timetable is retrieved.
   - The scraper processes the HTML using BeautifulSoup to extract relevant details such as activity names, times, dates, and locations.

2. **Calendar Generation**:
   - The extracted data is transformed into events for each week.
   - These events are formatted and stored in an `.ics` file, generated using the `ics` Python library.

3. **FastAPI Web Interface**:
   - The FastAPI framework handles HTTP requests, serving the static HTML form for Student ID input and generating `.ics` files upon form submission.

## Example

Input your QMUL Student ID into the form, click submit, and you'll get a personalized calendar file like this:

```plaintext
Event: Lecture - Computer Science
Date: Monday, September 25th, 2024
Time: 10:00 AM - 11:00 AM
Location: Engineering Building Room 103
```

## Contributing

If you want to contribute to this project:

1. Fork the repository.
2. Create a new feature branch.
3. Submit a pull request describing your changes.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.
