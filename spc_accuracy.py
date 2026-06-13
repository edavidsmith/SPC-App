import sqlite3
import requests
from zipfile import ZipFile
import geopandas as gpd
import folium
from shapely.geometry import Polygon
import string
from pathlib import Path
import os
import datetime
import sys

def test_url(url):
    try:
        response = requests.head(url)
        if response.status_code == 200:
            return True
        else:
            return False
    except requests.ConnectionError as e:
        return e

def download_archived_forecast(date):
    #checks if file already exists, and downloads if it does
    date_reformat = date.replace("-","")

    archive_url = f"https://www.spc.noaa.gov/products/outlook/archive/{date[:4]}/day1otlk_{date_reformat}_1300-shp.zip"
    needed_file = f"day1otlk_{date_reformat}_1300_torn.shp"
    needed_dir = f"forecasts\\{date[:4]}\\{date[5:7]}\\{date[8:]}"
    target_dir = Path(needed_dir)

    # print(test_url(f"https://www.spc.noaa.gov/exper/archive/event.php?date={date_reformat}"))
    # print(test_url(archive_url))

    if test_url(archive_url) != True:
        sys.exit("Error retrieving URL. Webpage may not exist.")

    if not target_dir.is_dir():
        target_dir.mkdir(parents=True, exist_ok = True)
        contents_archive_url = requests.get(archive_url) 
        with open("spcarchive.zip", mode="wb") as file:
            file.write(contents_archive_url.content)
        print("Archive downloaded")
        return needed_dir, True
    else:
        print("Necessary files already in directory")
        return f"{needed_dir}\\{needed_file}", False

def zip_file_extraction(zip_loc):
    with ZipFile("spcarchive.zip", 'r') as myzip:
        file_list = myzip.namelist()
        for i in file_list:
            if "torn" in i:
                if "shp" in i and not "sig" in i:
                    name_of_file = i
                myzip.extract(i, path=zip_loc)
    
    return f"{zip_loc}\\{name_of_file}"

def tor_coords_from_date(date):
    #plots tornado tracks as red lines on map
    con = sqlite3.connect("tornado-data\\tornado-events.db")
    cur = con.cursor()
    tracks = []
    labels = []
    for row in cur.execute(f'SELECT slat, slon, elat, elon, mag FROM tornadoes WHERE date = "{date}"'):
        tracks.append([[row[0], row[1]], [row[2], row[3]]])
        labels.append(row[4])
    return tracks, labels

def plot_tor_tracks(folium_object, tracks):
    #due to the nature of PolyLine, must plot every 2 pairs of coords, or else every single line will connect to one another
    tracks_list = tracks[0]
    labels = tracks[1]
    inc = 0
    for track in tracks_list:
        folium.PolyLine(
            locations=track,
            color="#FF0000",
            weight=3,
            tooltip="EF" + str(labels[inc]),
        ).add_to(folium_object)
        inc+=1

def plot_risk_polygon(folium_object, coord_list, risk_percent):
    color_dict = {"General Thunderstorm Risk" : "light green",
                  "2% Tornado Risk": "green", 
                  "5% Tornado Risk": "brown", 
                  "10% Tornado Risk": "yellow", 
                  "15% Tornado Risk": "red", 
                  "30% Tornado Risk": "pink", 
                  "45% Tornado Risk": "purple", 
                  "60% Tornado Risk": "blue"}
    
    #check if character exists in designation (i.e 5B), obtains only the numerical part
    if risk_percent[-1] in string.ascii_uppercase:
        risk_percent = risk_percent[:-1]
    
    #matches numerical part of color_dict to the truncated risk_percent
    risk_label = ""
    for key in color_dict.keys():
        if str(risk_percent) == key[:key.find("%")]:
                risk_label = key
    if risk_percent == "0":
        risk_label = "General Thunderstorm Risk"

    folium.Polygon(
        locations=coord_list,
        color="black",
        weight=1,
        fill_color= color_dict[risk_label],
        fill_opacity=0.2,
        fill=True,
        popup=risk_label,
        tooltip=risk_label,
        ).add_to(folium_object)

def poly_area(coords):
    poly = Polygon(coords)
    return poly.area
      
def create_comparison_map(date): #is not currently handling hatched areas, nor multipolygons; will handle in future
    #check if file has been downloaded before
    download_check = download_archived_forecast(date)
    if not download_check[1]:
        shp_file_name = download_check[0]
    else:
        shp_file_name = zip_file_extraction(download_check[0])

    shape_file = gpd.read_file(shp_file_name).to_crs(epsg=4326)
    shape_dict = shape_file.to_geo_dict()
    gdf = gpd.GeoDataFrame.from_features(shape_dict["features"])

    m = folium.Map(location=[40,-96], zoom_start=4)
    count_key_occur = []
    char_start = 66 #ASCII character for 'B'
    percent_risk_coords2 = {}

    for index in range(len(gdf)):
        outer_list = []
        count_key_occur.append(str(gdf.iat[index, 1]))
        for y,x in gdf.iat[index,0].exterior.coords:
            inner_list = []
            inner_list.extend([x, y]) 
            outer_list.append(inner_list)

        #check if key already exists, creates a new one with letter appended (i.e 5B) if it does
        if count_key_occur.count(str(gdf.iat[index, 1])) > 1:
            char_B_thr_Z = chr(char_start)
            percent_risk_coords2[f"{str(gdf.iat[index, 1])}{char_B_thr_Z}"] = outer_list
            char_start+=1
        else:
            percent_risk_coords2[str(gdf.iat[index, 1])] = outer_list
    
    #sort items by polygon area (largest first) and rebuild dictionary, prevents tooltips overlapping one another later
    percent_risk_coords2 = {
    k: v
    for k, v in sorted(
        percent_risk_coords2.items(),
        key=lambda item: poly_area(item[1]),
        reverse=True
    )
    }

    #handles inconsistent labeling scheme in SPC geodataframes
    if "DN" in gdf:
        for risk,coord in percent_risk_coords2.items():
            plot_risk_polygon(m, coord, str(risk))
    else:
        for risk,coord in percent_risk_coords2.items():
            perc_ind = risk.find("%")
            plot_risk_polygon(m, coord, str(risk[:perc_ind]))

    coord_list = tor_coords_from_date(date)
    plot_tor_tracks(m, coord_list)

    m.save("map-output\\map.html")

if __name__ == "__main__":
    #2011-04-27 is a good test date
    while True:
        date = input("Enter date using format YYYY-MM-DD. Use a date between 2009-01-06 and 2024-09-09 (data does not exist outside of this window): ")
        try:
            #checks if date is formatted correctly by attempting conversion to date object
            min_date = datetime.datetime.strptime("2009-01-06", "%Y-%m-%d").date()
            max_date = datetime.datetime.strptime("2024-09-09", "%Y-%m-%d").date()
            parsed_date = datetime.datetime.strptime(date, "%Y-%m-%d").date()

            if not min_date <= parsed_date <= max_date:
                print("Retry using a date between the specified window.")
                continue

            break 
        except ValueError:
            print("Date formatting incorrect. Try again.")

    create_comparison_map(date)
    for file in os.listdir():
        if file.endswith(".zip"):
            os.remove(file)
