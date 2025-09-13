from datetime import datetime, timezone
import requests
from zipfile import ZipFile

def download_zip_file(desired_zipfilename):
    # STEP 2: a zip file for download is located, utilizing knowledge of the SPC's predictable URL naming conventions
    day1_zulu = (100, 600, 1300, 1630, 2000)
    time = datetime.now(timezone.utc)
    time_replace = time.isoformat(timespec='milliseconds').replace('+00:00', 'Z')
    formatted_zulu_time = time_replace[11:16].replace(":", '')  # the time in zulu
    today_date = datetime.today().strftime('%Y-%m-%d').replace("-", "")  # today's date as YYYYMMDD

    # grabs what the most current outlook time SHOULD be
    for i in day1_zulu:
        if int(formatted_zulu_time) >= i:
            current_day1_outlook_time = i

    full_url = f"https://www.spc.noaa.gov/products/outlook/archive/{today_date[:4]}/day1otlk_{today_date}_{current_day1_outlook_time:04d}-shp.zip"
    source_zip_file = requests.get(full_url)

    # if current_day1_outlook_time is not up to date yet, uses previous zulu time
    if source_zip_file.status_code != 200:
        fixed_outlook_index = day1_zulu.index(current_day1_outlook_time) - 1
        full_url = f"https://www.spc.noaa.gov/products/outlook/archive/{today_date[:4]}/day1otlk_{today_date}_{day1_zulu[fixed_outlook_index]:04d}-shp.zip"
        source_zip_file = requests.get(full_url)

    with open(desired_zipfilename, mode="wb") as file:
        file.write(source_zip_file.content)

def zip_file_iteration(zipfilename, user_specified_outlook):
    # STEP 3: iterate over contents of downloaded .zip file, making sure to only extract what is necessary based on user's specification
    with ZipFile(zipfilename, 'r') as myzip:
        file_list = myzip.namelist()

        # only necessary files are extracted based on desired outlook
        for i in file_list:
            if user_specified_outlook == "categorical" and "cat" in i:
                if "shp" in i:
                    name_of_desired = i
                myzip.extract(i)
            if user_specified_outlook == "hail" and not "sig" in i and "hail" in i:
                if "shp" in i:
                    name_of_desired = i
                myzip.extract(i)
            if user_specified_outlook == "tornado" and not "sig" in i and "torn" in i:
                if "shp" in i:
                    name_of_desired = i
                myzip.extract(i)
            if user_specified_outlook == "wind" and not "sig" in i and "wind" in i:
                if "shp" in i:
                    name_of_desired = i
                myzip.extract(i)

        return name_of_desired
