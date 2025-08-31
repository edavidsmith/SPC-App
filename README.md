# Storm Prediction Center Convective Outlook Checker 

## Description
This program takes a user-entered city from input and then tells the user what categorical risk level that city is located in for the day. 

## Features 
- Uses a geocoding API to convert user-entered town or city into coordinates
- Downloads .zip folder from the SPC's website, then extracts required contents from archive
- Parses geospatial data from the .shp file and identifies which risk area the user-entered coordinates are in
- Deletes all files once program has finished running

## Planned Features
- Allow the user to see their day 2 and beyond outlook if they wish
- Allow the user to see other convective risk outlooks, not just categorical (e.g. tornado risk, hail risk, wind risk etc.)
- Expand the program into a weather focused travel-planning app, allowing the user to enter two locations, automatically map a route, and then tell them what convective outlook areas their route goes through
- Eventually create a GUI