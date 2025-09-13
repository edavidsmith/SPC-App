import requests
from shapely.geometry import Point
import geopandas as gpd
import os
import my_file_handling

def city_to_coordinates(city):
    # STEP 1: a city is converted to coordinates in this function
    url = "https://nominatim.openstreetmap.org/search?"
    params = "addressdetails=1&q=" + city.replace(" ", "+") + "&format=jsonv2"
    full_url = url + params
    response = requests.get(full_url, headers={"User-Agent": "SPCapp (dastardlycakev4@gmail.com)"})
    json = response.json()

    lat = json[0]['lat']
    lon = json[0]['lon']

    return {"latitude": lat, "longitude": lon, "city-name": city}

def shape_file_parsed():
    # STEP 4: the .shp file extracted from earlier is parsed and used to tell the user what risk area their specified city is in
    city = city_to_coordinates(input("Enter a city: "))
    user_query_which_outlook = input(
        "Which type of outlook do you wish to view? (categorical,tornado,hail,wind): ").lower().strip()

    # loop handles bad input
    accepted_input = ("categorical", "tornado", "hail", "wind")
    while user_query_which_outlook not in accepted_input:
        user_query_which_outlook = input(
            "Input not accepted. Which type of outlook do you wish to view? (categorical,tornado,hail,wind): ").lower().strip()

    zip_file_name = "spcdata.zip"
    my_file_handling.download_zip_file(zip_file_name)
    name_of_file = my_file_handling.zip_file_iteration(zip_file_name, user_query_which_outlook)

    shape_file = gpd.read_file(name_of_file)
    shape_dict = shape_file.to_geo_dict()
    gdf = gpd.GeoDataFrame.from_features(
        shape_dict["features"])  # the features (ie coordinates) from the extacted shp file are accessed

    coord_to_use = gpd.GeoSeries([Point(city["longitude"], city["latitude"])], crs="EPSG:3857")
    gdf.set_crs("EPSG:3857", inplace=True)

    risk_exists = False
    for num, i in enumerate(gdf.contains(coord_to_use[0])):
        if i == True:
            num_caught = num
            risk_exists = True

    if not risk_exists:
        print("No storm risks today")
    else:
        risk_name = gdf.loc[
            num_caught, "LABEL2"]  # based on the Integer label that evaluated "True" for .contains(), its corresponding String risk label is accessed thus
        print(
            f"For today's {user_query_which_outlook} convective outlook in {city["city-name"]}, there is a {risk_name} in place")

def main():
    shape_file_parsed()
    protected_files = ["spc_main.py", "my_file_handling.py", "README.md", ".gitignore"]

    for i in os.listdir():
        if i not in protected_files and not os.path.isdir(i):
            os.remove(i)

if __name__ == "__main__":
    main()