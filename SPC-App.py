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
    

def ZipFileIteration(filename, user_specified_outlook):
    with ZipFile(filename,'r') as myzip:
        file_list = myzip.namelist()

        #only necessary files are extracted based on desired outlook
        for i in file_list:
            if user_specified_outlook == "cat" and "cat" in i:
                if "shp" in i:
                    name_of_desired = i
                myzip.extract(i)
            if user_specified_outlook == "hail" and not "sig" in i and "hail" in i:
                if "shp" in i:
                    name_of_desired = i
                myzip.extract(i)
            if user_specified_outlook == "tor" and not "sig" in i and "torn" in i:
                if "shp" in i:
                    name_of_desired = i
                myzip.extract(i)
            if user_specified_outlook == "wind" and not "sig" in i and "wind" in i:
                if "shp" in i:
                    name_of_desired = i
                myzip.extract(i)

        return name_of_desired

def ShapeFileComparison(user_query_which_outlook):
    city = CityToCoord(input("Enter a city: "))
    zip_file_name = "spcdata.zip"
    GetZipFromHTML("https://www.spc.noaa.gov/products/outlook/day1otlk.html", "shp.zip","https://www.spc.noaa.gov","/","zip",3,zip_file_name)
    name_of_file = ZipFileIteration(zip_file_name,user_query_which_outlook)

    shape_file = gpd.read_file(name_of_file) 
    
    shape_dict = shape_file.to_geo_dict()

    gdf = gpd.GeoDataFrame.from_features(shape_dict["features"])
    coord_to_use = gpd.GeoSeries([Point(city["longitude"],city["latitude"])], crs="EPSG:3857")
    gdf.set_crs("EPSG:3857", inplace=True)
    

    risk_exists = False
    for num,i in enumerate(gdf.contains(coord_to_use[0])):
        if i == True:
            num_caught = num
            risk_exists = True

    if not risk_exists:
        num_caught = 9 #basic way of handling situations where there are no storm risks, may refine later

    return num_caught
    
#for wind risks 0 means 5% risk. After, it goes from 15%, in increments of 15 up to 60%. Use accordingly
#same as above for hail risk
def RiskAreaName(risk_area_number,user_specified_risk):
    match risk_area_number:
        case 0:
            if user_specified_risk == "cat":
                return "General thunderstorm risk"
            elif user_specified_risk == "wind":
                return "5% wind risk"
            elif user_specified_risk == "hail":
                return "5% hail risk"
            elif user_specified_risk == "tor":
                return "2% tornado risk"
        case 1:
            if user_specified_risk == "cat":
                return "Marginal risk"
            elif user_specified_risk == "wind":
                return "15% wind risk"
            elif user_specified_risk == "hail":
                return "15% hail risk"
            elif user_specified_risk == "tor":
                return "5% tornado risk"
        case 2:
            if user_specified_risk == "cat":
                return "Slight risk"
            elif user_specified_risk == "wind":
                return "30% wind risk"
            elif user_specified_risk == "hail":
                return "30% hail risk"
            elif user_specified_risk == "tor":
                return "15% tornado risk"
        case 3:
            if user_specified_risk == "cat":
                return "Enhanced risk"
            elif user_specified_risk == "wind":
                return "45% wind risk"
            elif user_specified_risk == "hail":
                return "45% hail risk"
            elif user_specified_risk == "tor":
                return "30% tornado risk"
        case 4:
            if user_specified_risk == "cat":
                return "Moderate risk"
            elif user_specified_risk == "wind":
                return "60% wind risk"
            elif user_specified_risk == "hail":
                return "60% hail risk"
            elif user_specified_risk == "tor":
                return "45% tornado risk"
        case 5:
            if user_specified_risk == "cat":
                return "High risk"
            elif user_specified_risk == "wind":
                return "Significant wind risk (highest possible wind risk)"
            elif user_specified_risk == "hail":
                return "Significant hail risk (highest possible wind risk)"
            elif user_specified_risk == "tor":
                return "60% tornado risk"
        case 6:
            return "Significant tornado risk (highest possible tornado risk)" #the only case where integers 6 could be returned are for tornado risks
        case 9:
            return "No storm risks"

def main():
    user_query_which_outlook = input("Which outlook do you wish to view? (cat,tor,hail,wind): ")
    print(RiskAreaName(ShapeFileComparison(user_query_which_outlook),user_query_which_outlook))

    protected_files = ["SPC-App.py", "README.md", ".gitignore"]

    for i in os.listdir():
        if i not in protected_files and not os.path.isdir(i):
            os.remove(i)

if __name__ == "__main__":
    main()