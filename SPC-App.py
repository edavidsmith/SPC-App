import requests
from zipfile import ZipFile
from shapely.geometry import Point
import geopandas as gpd
import os
from datetime import datetime
from datetime import timezone

def CityToCoordinates(city):
    #STEP 1: a city is converted to coordinates in this function
    url = "https://nominatim.openstreetmap.org/search?"
    params = "addressdetails=1&q=" + city.replace(" ","+") + "&format=jsonv2"
    full_url = url + params
    response = requests.get(full_url, headers={"User-Agent": "SPCapp (dastardlycakev4@gmail.com)"})
    json = response.json()

    lat = json[0]['lat']
    lon = json[0]['lon']

    return {"latitude": lat, "longitude": lon, "city-name": city}

def DownloadZipFile(desired_zipfilename):
    #STEP 2: a zip file for download is located, utilizing knowledge of the SPC's predictable URL naming conventions
    day1_zulu = (100,600,1300,1630,2000)
    time = datetime.now(timezone.utc)
    time_replace = time.isoformat(timespec='milliseconds').replace('+00:00', 'Z')
    formatted_zulu_time = time_replace[11:16].replace(":",'') #the time in zulu
    today_date = datetime.today().strftime('%Y-%m-%d').replace("-","") #today's date as YYYYMMDD
    
    #grabs what the most current outlook time SHOULD be
    for i in day1_zulu:
        if int(formatted_zulu_time) >= i:
            current_day1_outlook_time = i

    full_url = f"https://www.spc.noaa.gov/products/outlook/archive/{today_date[:4]}/day1otlk_{today_date}_{current_day1_outlook_time:04d}-shp.zip"
    source_zip_file = requests.get(full_url)

    #if current_day1_outlook_time is not up to date yet, uses previous zulu time
    if source_zip_file.status_code != 200:
        fixed_outlook_index = day1_zulu.index(current_day1_outlook_time) - 1
        full_url = f"https://www.spc.noaa.gov/products/outlook/archive/{today_date[:4]}/day1otlk_{today_date}_{day1_zulu[fixed_outlook_index]:04d}-shp.zip"
        source_zip_file = requests.get(full_url)

    with open(desired_zipfilename, mode="wb") as file:
        file.write(source_zip_file.content)
    

def ZipFileIteration(zipfilename, user_specified_outlook):
    #STEP 3: iterate over contents of downloaded .zip file, making sure to only extract what is necessary based on user's specification
    with ZipFile(zipfilename,'r') as myzip:
        file_list = myzip.namelist()

        #only necessary files are extracted based on desired outlook
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

def ShapeFileParsed():
    #STEP 4: the .shp file extracted from earlier is parsed and used to tell the user what risk area their specified city is in
    city = CityToCoordinates(input("Enter a city: "))
    user_query_which_outlook = input("Which type of outlook do you wish to view? (categorical,tornado,hail,wind): ").lower().strip()
    
    #loop handles bad input
    accepted_input = ("categorical","tornado","hail","wind")
    while user_query_which_outlook not in accepted_input:
        user_query_which_outlook = input("Input not accepted. Which type of outlook do you wish to view? (categorical,tornado,hail,wind): ").lower().strip()

    zip_file_name = "spcdata.zip"
    DownloadZipFile(zip_file_name)
    name_of_file = ZipFileIteration(zip_file_name,user_query_which_outlook)

    shape_file = gpd.read_file(name_of_file) 
    shape_dict = shape_file.to_geo_dict()
    gdf = gpd.GeoDataFrame.from_features(shape_dict["features"]) #the features (ie coordinates) from the extacted shp file are accessed

    coord_to_use = gpd.GeoSeries([Point(city["longitude"],city["latitude"])], crs="EPSG:3857")
    gdf.set_crs("EPSG:3857", inplace=True)

    risk_exists = False
    for num,i in enumerate(gdf.contains(coord_to_use[0])):
        if i == True:
            num_caught = num
            risk_exists = True

    if not risk_exists:
        print("No storm risks today")
    else:
        risk_name = gdf.loc[num_caught,"LABEL2"] #based on the Integer label that evaluated "True" for .contains(), its corresponding String risk label is accessed thus
        print(f"For today's {user_query_which_outlook} convective outlook in {city["city-name"]}, there is a {risk_name} in place")

def main():
    ShapeFileParsed()
    protected_files = ["SPC-App.py", "README.md", ".gitignore"]

    for i in os.listdir():
        if i not in protected_files and not os.path.isdir(i):
            os.remove(i)

if __name__ == "__main__":
    main()