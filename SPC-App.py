import requests
from bs4 import BeautifulSoup
import re
from zipfile import ZipFile
import geopandas
from shapely.geometry import Point
import geopandas as gpd
import os

def StartToEnd(string,startchar,endchar,amounttoadd = 0):
    start = string.find(startchar)
    end = string.find(endchar) + amounttoadd

    return string[start:end]

def CityToCoord(city):
    url = "https://nominatim.openstreetmap.org/search?"
    params = "addressdetails=1&q=" + city.replace(" ","+") + "&format=jsonv2"
    full_url = url + params
    response = requests.get(full_url, headers={"User-Agent": "SPCapp (dastardlycakev4@gmail.com)"})
    json = response.json()

    lat = json[0]['lat']
    lon = json[0]['lon']

    return {"latitude": lat, "longitude": lon}

def GetZipFromHTML(SourceSite, FindInHTML, URL_begin, param1,param2,param3,desired_filename):
    sourceHTML = requests.get(SourceSite)
    rawtext = sourceHTML.text

    html = BeautifulSoup(rawtext,"html.parser")

    line_found = html.find_all(href=re.compile(FindInHTML)) #shp.zip in our case
    line_string = str(line_found[0])

    EndOfUrl = StartToEnd(line_string,param1,param2,param3) 
    source_zip_file = requests.get(URL_begin + EndOfUrl)

    with open(desired_filename, mode="wb") as file:
        file.write(source_zip_file.content)
    

def ZipFileIteration(filename):
    with ZipFile(filename,'r') as myzip:
        file_list = myzip.namelist()

        for i in file_list:
            if "cat.shp" in i:
                name_of_catfile = i
            if "hail.shp" in i:
                name_of_hailfile = i
            if "torn.shp" in i:
                name_of_tornfile = i
            if "wind.shp" in i:
                name_of_windfile = i
            myzip.extract(i)


        return {"cat": name_of_catfile,"hail": name_of_hailfile,"tor": name_of_tornfile, "wind": name_of_windfile} #returns the shape file for each respective outlook in a dictionary

def ShapeFileComparison():
    city = CityToCoord(input("Enter a city: "))
    zip_file_name = "spcdata.zip"
    GetZipFromHTML("https://www.spc.noaa.gov/products/outlook/day1otlk.html", "shp.zip","https://www.spc.noaa.gov","/","zip",3,zip_file_name)
    name_of_file = ZipFileIteration(zip_file_name)

    user_query_which_outlook = input("Which outlook do you wish to view? (cat,tor,hail,wind): ")
    shape_file = geopandas.read_file(name_of_file.get(user_query_which_outlook)) 
    
    shape_dict = shape_file.to_geo_dict()
    print(shape_dict)


    gdf = gpd.GeoDataFrame.from_features(shape_dict["features"])
    coord_to_use = geopandas.GeoSeries([Point(city["longitude"],city["latitude"])], crs="EPSG:3857")
    gdf.set_crs("EPSG:3857", inplace=True)
    print("Does it get this far at least?") #it does get this far

    risk_exists = False
    for num,i in enumerate(gdf.contains(coord_to_use[0])): #when the city is not in a risk area, there will be an error inevitably 
        print(i)
        if i == True:
            num_caught = num
            risk_exists = True

    if(not risk_exists):
        num_caught = 9 #basic way of handling when there are no storm risks, may refine later

    print(num_caught)
    return num_caught

def RiskAreaName(risk_area_number):
    match risk_area_number:
        case 0:
            return "General thunderstorm risk"
        case 1:
            return "Marginal risk"
        case 2:
            return "Slight risk"
        case 3:
            return "Enhanced risk"
        case 4:
            return "Moderate risk"
        case 5:
            return "High risk"
        case 9:
            return "No storm risks"

def main():
    print(RiskAreaName(ShapeFileComparison()))

    protected_files = ["SPC-App.py", "README.md", ".gitignore"]

    for i in os.listdir():
        if i not in protected_files and not os.path.isdir(i):
            os.remove(i)

if __name__ == "__main__":
    main()