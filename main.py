# Standard Libraries
from datetime import datetime, timedelta
from tempfile import NamedTemporaryFile
import base64

# FastAPI and Pydantic for web and data validation
from fastapi import FastAPI, HTTPException, Form
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path


# Selenium for web scraping
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# BeautifulSoup for HTML parsing
from bs4 import BeautifulSoup

# ICS library for calendar generation
from ics import Calendar, Event

def main(studentID=''):
    try:
        if studentID == '':
            raise ValueError(f"Missing required fields: studentID")
    except ValueError as err:
        return [{"ok": False, "error": str(err)}, 400]
    
    try:
        # Extract the student number from the request
        student_number = studentID

        # Set up Selenium with Chrome options for headless mode
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        # Connect to the Browserless Docker instance
        driver = webdriver.Remote(
            command_executor='http://localhost:3000/webdriver', 
            options=chrome_options
        )

        try:
            # Navigate to the timetable page
            driver.get('https://timetables.qmul.ac.uk/default.aspx')
            link = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, 'LinkBtn_studentsetstaff'))
            )
            link.click()

            # Enter the student ID
            input_field = driver.find_element(By.ID, 'tObjectInput')
            input_field.clear()
            input_field.send_keys(student_number)

            # Select the options for days, periods, and type
            Select(driver.find_element(By.ID, 'lbDays')).select_by_visible_text('All Weekdays')
            Select(driver.find_element(By.ID, 'dlPeriod')).select_by_visible_text('Teaching Day (08:00 - 18:00)')
            Select(driver.find_element(By.ID, 'dlType')).select_by_visible_text('List Timetable')

            # Click the "Get Timetable" button
            get_timetable_button = driver.find_element(By.ID, 'bGetTimetable')
            get_timetable_button.click()

            # Wait for the timetable to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'header-0-0-0'))
            )

            # Get the HTML content
            html_content = driver.page_source
            soup = BeautifulSoup(html_content, 'html.parser')

            # Create a new calendar
            calendar = Calendar()

            # Week 8 starts on 23rd September 2024, so we define the base date for week 8
            week_8_date = datetime.strptime("23 Sep 2024", "%d %b %Y")

            # Function to parse week ranges like '8-19' or '26, 29, 33, 36'
            def parse_weeks(week_str):
                weeks = []
                for part in week_str.split(','):
                    if '-' in part:
                        start, end = map(int, part.split('-'))
                        weeks.extend(range(start, end + 1))
                    else:
                        weeks.append(int(part.strip()))
                return weeks

            # Helper function to format time with leading zeros if necessary
            def format_time(time_str):
                # Ensure times like "9:00" become "09:00"
                return datetime.strptime(time_str, '%H:%M').strftime('%H:%M')

            # Iterate over each day's schedule and add events to the calendar
            days = soup.find_all('span', class_='labelone')
            tables = soup.find_all('table', class_='spreadsheet')

            for day, table in zip(days, tables):
                day_name = day.text.strip()
                rows = table.find_all('tr')[1:]  # Skip the header row
                for row in rows:
                    columns = row.find_all('td')
                    activity_name = columns[0].text.strip()
                    activity_type = columns[2].text.strip()
                    start_time = format_time(columns[3].text.strip())
                    end_time = format_time(columns[4].text.strip())
                    weeks = parse_weeks(columns[5].text.strip())
                    location = columns[6].text.strip().replace('Location: ', '')
                    staff = columns[7].text.strip()

                    for week in weeks:
                        event = Event()
                        event.name = activity_name
                        event.description = f"{activity_type} - {staff}"
                        event.location = location

                        # Calculate the date for this event
                        event_date = week_8_date + timedelta(weeks=week - 8)
                        # Adjust the date to match the correct day of the week
                        weekday_index = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"].index(day_name)
                        event_date += timedelta(days=weekday_index)

                        # Combine date and time for start and end
                        event.begin = event_date.strftime('%Y-%m-%d') + f" {start_time}"
                        event.end = event_date.strftime('%Y-%m-%d') + f" {end_time}"
                        event.make_all_day = False

                        calendar.events.add(event)

            # Export calendar to an ICS file in memory
            ics_content = str(calendar)
            ics_encoded = base64.b64encode(ics_content.encode()).decode()

            # Return the ICS file as a string        
            return [{"ok": True, "ics_base64": ics_encoded}, 200]

        finally:
            driver.quit()

    except Exception as e:
        return [{"ok": False, "error": str(e)}, 500]


# FastAPI app initialization
app = FastAPI()

# Serve the static files (CSS, JS, etc.) from the "static" directory
app.mount("/static", StaticFiles(directory="static"), name="static")

favicon_path = 'favicon.ico'

# Serve the index.html file when accessing the root ("/")
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def serve_index():
    index_path = Path("static/index.html")
    return index_path.read_text()

@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return FileResponse(favicon_path)

# Endpoint to generate the ICS file and return it for download
@app.post("/generate-ics")
async def generate_ics(studentID: str = Form(...)):
    try:
        # Call the main function with the provided studentID
        result = main(studentID=studentID)
        if result[0]["ok"]:
            # Decode the base64-encoded ICS content
            ics_content = base64.b64decode(result[0]["ics_base64"])

            # Save it temporarily as an .ics file
            with NamedTemporaryFile(delete=False, suffix=".ics") as temp_file:
                temp_file.write(ics_content)
                temp_file_path = temp_file.name

            # Return the .ics file as a downloadable response
            return FileResponse(path=temp_file_path, filename="timetable.ics", media_type='text/calendar')
        else:
            raise HTTPException(status_code=400, detail=result[0]["error"])
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred while generating the ICS file")


# To test run, use Uvicorn's ASGI server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)