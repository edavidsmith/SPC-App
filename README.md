# Storm Prediction Center Convective Outlook Checker 

## Description
This program allows a user to specify a city and a type of convective risk, then tells them the outlook for that city based on data from NOAA

## Features 
- Uses a geocoding API to convert user-entered town or city into coordinates
- Downloads .zip folder from SPC webpage, then extracts required contents from archive
- Parses geospatial data from the .shp file and identifies which risk area the user-entered coordinates are in
- Deletes all files once program has finished running

## Planned Features
- Allow the user to see their day 2 and beyond outlook if they wish
- Expand the program into a weather focused travel-planning app, allowing the user to enter two locations, automatically map a route, and then tell them what convective outlook areas their route goes through
- Eventually create a GUI