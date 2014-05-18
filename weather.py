#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Write some message on the display.
# This project uses https://github.com/dbrgn/RPLCD.
# sudo apt-get install python-matplotlib

from __future__ import print_function, division, absolute_import, unicode_literals

import sys

# Import LCD stuff from RPLCD, et. al.
from RPLCD import CharLCD
from RPLCD import Alignment, CursorMode, ShiftMode
from RPLCD import cursor, cleared

from xml.dom.minidom import *
import urllib
import RPi.GPIO as GPIO
import time
import csv

import os
import subprocess
import shutil


# some LCD magic happens here
try:
    input = raw_input
except NameError:
    pass

try:
    unichr = unichr
except NameError:
    unichr = chr

# ###################################################################################
# Configure stuff here:
# Temp sensor ID is the folder name for ds18b20 1-wire sensors
# found in /sys/bus/w1/devices/
# Drivers are loaded with
# sudo modprobe w1-gpio
# sudo modprobe w1-therm
# or put them in /etc/modules
Temp_Sensor_Inside = '28-000005ad1070'
Temp_Sensor_Outside = '28-000005ad0691'
# Yahoo location code. Get the right one for your location from Yahoo's weather page.
Location_ID = '700029'
# ###################################################################################

# Disable useless GPIO warnings
GPIO.setwarnings(False)

# Start Yahoo weather stuff
# Weather array
# Dimensions: 1 = today, 2 = tomorrow
# Elements: 1 = day, 2 = date, 3 = low temp, 4 = high temp, 5 = weather text
Weather_Array = [["", "", "", "", ""] , ["", "", "", "", ""]]

# Fetch weather XML for Trier, Germany
Trier = urllib.urlopen('http://weather.yahooapis.com/forecastrss?w=' + Location_ID + '&u=c').read()

# Parse the XML
Trier = parseString(Trier)

# Get town
Place = Trier.getElementsByTagName('yweather:location')[0]
City = Place.attributes["city"].value
Country = Place.attributes["country"].value

# Get date
Date = Trier.getElementsByTagName('lastBuildDate')[0].firstChild.data

# Get coordinates
Geo_Lat = Trier.getElementsByTagName('geo:lat')[0].firstChild.data
Geo_Long = Trier.getElementsByTagName('geo:long')[0].firstChild.data

# Get today's weather
Today = Trier.getElementsByTagName('yweather:condition')[0]
Weather_Text = Today.attributes["text"].value
Temperature = float(Today.attributes["temp"].value)
Condition_Code = Today.attributes["code"].value

# Put it all in a list
for Counter in range(2):

    # Weather data for two days
    # Get data
    Future = Trier.getElementsByTagName('yweather:forecast')[Counter]

    # Process data
    Weather_Array[Counter][0] = Future.attributes["day"].value
    Weather_Array[Counter][1] = Future.attributes["date"].value
    Weather_Array[Counter][2] = float(Future.attributes["low"].value)
    Weather_Array[Counter][3] = float(Future.attributes["high"].value)
    Weather_Array[Counter][4] = Future.attributes["text"].value
# End Yahoo weather stuff.

# Start sensor stuff
# The inside sensor
# Open, read, close the sensor files
Temp_File_In = open("/sys/bus/w1/devices/" + Temp_Sensor_Inside + "/w1_slave")

Text_In = Temp_File_In.read()

Temp_File_In.close()

# Jump to the right position in the sensor file, convert the string to a number, put the decimal point in
Second_Line_In = Text_In.split("\n")[1]
Temperature_Data_In = Second_Line_In.split(" ")[9]
Temperature_In = float(Temperature_Data_In[2:])
Temperature_In = Temperature_In / 1000
# print Temperature_In

# The outside sensor
Temp_File_Out = open("/sys/bus/w1/devices/" + Temp_Sensor_Outside + "/w1_slave")

Text_Out = Temp_File_Out.read()

Temp_File_Out.close()

# Jump to the right position in the sensor file, convert the string to a number, put the decimal point in
Second_Line_Out = Text_Out.split("\n")[1]
Temperature_Data_Out = Second_Line_Out.split(" ")[9]
Temperature_Out = float(Temperature_Data_Out[2:])
Temperature_Out = Temperature_Out / 1000
# print Temperature_Out

lcd = CharLCD()


# Print the data onto the display.
lcd.clear()
lcd.write_string(time.strftime("%d.%m.%Y %H:%M"))
lcd.cursor_pos = (1, 0)
#lcd.write_string(str(City) + ' ')
lcd.write_string('Innen:  '+ str(Temperature_In) + ' Grad')
lcd.cursor_pos = (2, 0)
lcd.write_string('Aussen: '+ str(Temperature_Out) + ' Grad')
lcd.cursor_pos = (3, 0)
lcd.write_string(Weather_Text)

# Write the data to a webpage on the local server
# Get some weather icons that are compliant with Yahoo condition codes. The ones by MerlinTheRed are nice and work well <http://merlinthered.deviantart.com/art/plain-weather-icons-157162192> CC-BY-NC-SA
index = open('/var/www/aktuell.html','w')
index.write('<style type="text/css">body {font-weight:lighter; font-family:Arial; font-size:100%; } h2 {margin:0 0 0 0;} h6 {margin:0 0 0 0;}</style><h6>Updated: ' + time.strftime("%d.%m.%Y %H:%M:%S") + '</h6>' + Weather_Text + '<img src="' + Condition_Code + '.png" align="right" alt="Wettericon"><br>Innen:<br><h2>' + str(Temperature_In) + ' &deg;C</h2><br> Aussen:<br><h2>' + str(Temperature_Out) + '&deg;C</h2><br>')
index.close()


 # Write data to a .csv file for graph creation
weather_csv = open('/home/pi/YAWP/weather.csv', 'a')
Data_Writer = csv.writer(weather_csv)
Data_Writer.writerow([str(time.strftime('%Y-%m-%d %H:%M')),str(Temperature_In),str(Temperature_Out),str('0'),str('15')])
weather_csv.close()

# From here, a gnuplot file will take over.
# Print graph for one day
p = subprocess.Popen("gnuplot plotter.gpi", shell = True)
os.waitpid(p.pid, 0)
# Print graph for one week
p = subprocess.Popen("gnuplot weekplotter.gpi", shell = True)
os.waitpid(p.pid, 0)

# Copy it over to the webserver
shutil.copy2('/home/pi/YAWP/temps.png', '/var/www/')
shutil.copy2('/home/pi/YAWP/weektemps.png', '/var/www/')




