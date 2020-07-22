
# my_forensics.py
# Python Forensic Evidence Extraction
# Author: L. Konate
# Fall 2019

#################################################################
# pfish support functions, where all the real work gets done
#
# Display Message() CommandLineInterface() WalkPath()
# HashFile() class _CVSWriter
# ValidateDirectory() ValidateDirectoryWritable()
#################################################################
# #
# GPS Extraction
# Python-Forensics
# No HASP required

import os
import _modEXIF
import _csvHandler
import _commandParser
from classLogging import _ForensicLog

def main():

    # Offsets into the return EXIFData for
    # TimeStamp, Camera Make and Model
    TS = 0
    MAKE = 1
    MODEL = 2
    # Process the Command Line Arguments
    userArgs = _commandParser.CommandLineInterface()
    # create a log object
    logPath = userArgs.logPath+"ForensicLog.txt"
    oLog = _ForensicLog(logPath)
    oLog.writeLog("INFO", "Scan Started")
    csvPath = userArgs.csvPath+"imageResults.csv"
    oCSV = _csvHandler._CSVWriter(csvPath)
    # define a directory to scan
    scanDir = userArgs.scanPath
    try:
        picts = os.listdir(scanDir)
    except:
        oLog.writeLog("ERROR", "Invalid Directory "+ scanDir)
        exit(0)

    print ("Program Start")
    print ()
    for aFile in picts:
        targetFile = scanDir+aFile
        if os.path.isfile(targetFile):
            gpsDictionary, EXIFList = _modEXIF.ExtractGPSDictionary (targetFile)
            if (gpsDictionary):
                # Obtain the Lat Lon values from the gpsDictionary
                # Converted to degrees
                # The return value is a dictionary key value pairs
                dCoor = _modEXIF.ExtractLatLon(gpsDictionary)
                lat = dCoor.get("Lat")
                latRef = dCoor.get("LatRef")
                lon = dCoor.get("Lon")
                lonRef = dCoor.get("LonRef")

                if ( lat and lon and latRef and lonRef):
                    print(str(lat)+','+str(lon))
                    # write one row to the output file
                    oCSV.writeCSVRow(targetFile, EXIFList[TS], EXIFList[MAKE], EXIFList[MODEL],latRef, lat, lonRef, lon)
                    oLog.writeLog("INFO", "GPS Data Calculated for :" + targetFile)
                else:
                    oLog.writeLog("WARNING", "No GPS EXIF Data for "+ targetFile)
            else:
                oLog.writeLog("WARNING", "No GPS EXIF Data for "+ targetFile)
        else:
            oLog.writeLog("WARNING", targetFile + " not a valid file")
    # Clean up and Close Log and CSV File
    del oLog
    del oCSV

import argparse # Python Standard Library - Parser for command-line options, arguments
import os # Standard Library OS functions
# Name: ParseCommand() Function
# Desc: Process and Validate the command line arguments
# use Python Standard Library module argparse
#
# Input: none
#
# Actions:
# Uses the standard library argparse to process the command line
#
def CommandLineInterface():
    parser = argparse.ArgumentParser('Python gpsExtractor')
    parser.add_argument('-v','--verbose', help="enables printing of additional program messages", action='store_true')
    parser.add_argument('-l','--logPath', type= ValidateDirectory,required=True, help="specify the directory for forensic log output file")
    parser.add_argument('-c','--csvPath', type= ValidateDirectory, required=True, help="specify the output directory for the csv file")
    parser.add_argument('-d','--scanPath', type= ValidateDirectory, required=True, help="specify the directory to scan")
    args = parser.parse_args()
    return args

# End Parse Command Line ===========================

def ValidateDirectory(theDir):
    # Validate the path is a directory
    if not os.path.isdir(theDir):
        raise argparse.ArgumentTypeError('Directory does not exist')
    # Validate the path is writable
    if os.access(theDir, os.W_OK):
        return theDir
    else:
        raise argparse.ArgumentTypeError('Directory is not writable')

#End ValidateDirectory ===================================

import logging
#
# Class: _ForensicLog
#
# Desc: Handles Forensic Logging Operations
#
# Methods constructor: Initializes the Logger
# writeLog: Writes a record to the log
# destructor: Writes an information message and shuts down the logger

class _ForensicLog:
    def __init__(self, logName):
        try:
            # Turn on Logging
            logging.basicConfig(filename=logName,level=logging.DEBUG,format='%(asctime)s %(message)s')
        except:
            print ("Forensic Log Initialization Failed . . . Aborting")
            exit(0)

    def writeLog(self, logType, logMessage):
        if logType == "INFO":
            logging.info(logMessage)
        elif logType == "ERROR":
            logging.error(logMessage)
        elif logType == "WARNING":
            logging.warning(logMessage)
        else:
            logging.error(logMessage)
        return
    
    def __del__(self):
        logging.info("Logging Shutdown")
        logging.shutdown()

#End _ForensicLog =========================================        

#
# Data Extraction - Python-Forensics
# Extract GPS Data from EXIF supported Images (jpg, tiff)
# Support Module
#

import os # Standard Library OS functions
from classLogging import _ForensicLog # Abstracted Forensic Logging Class
# import the Python Image Library
# along with TAGS and GPS related TAGS
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
#
# Extract EXIF Data
#
# Input: Full Pathname of the target image
#
# Return: gps Dictionary and selected EXIFData list
#
def ExtractGPSDictionary(fileName):
    try:
        pilImage = Image.open(fileName)
        EXIFData = pilImage._getexif()
    except Exception:
    # If exception occurs from PIL processing
    # Report the
        return None, None
    # Iterate through the EXIFData
    # Searching for GPS Tags
    imageTimeStamp = "NA"
    CameraModel = "NA"
    CameraMake = "NA"
    if EXIFData:
        for tag, theValue in EXIFData.items():
            # obtain the tag
            tagValue = TAGS.get(tag, tag)
            # Collect basic image data if available
            if tagValue =='DateTimeOriginal':
                imageTimeStamp = EXIFData.get(tag)
            if tagValue == "Make":
                cameraMake = EXIFData.get(tag)
            if tagValue =='Model':
                cameraModel = EXIFData.get(tag)
            # check the tag for GPS
            if tagValue == "GPSInfo":
                # Found it !
                # Now create a Dictionary to hold the GPS Data
                gpsDictionary = {}
                # Loop through the GPS Information
                for curTag in theValue:
                    gpsTag = GPSTAGS.get(curTag, curTag)
                    gpsDictionary[gpsTag] = theValue[curTag]
                    basicEXIFData = [imageTimeStamp, cameraMake, cameraModel]
        return gpsDictionary, basicEXIFData
    else:
        return None, None

# End ExtractGPSDictionary ============================

# Extract the Latitude and Longitude Values
# From the gpsDictionary
#
def ExtractLatLon(gps):
    # to perform the calculation we need at least
    # lat, lon, latRef and lonRef
    if ('gGPSLatitudeRef' in gps.keys() and 'GPSLatitude'in gps.keys() and 'GPSLongitudeRef'in gps.keys() and'GPSLongitude'in gps.keys()):
        latitude = gps["GPSLatitude"]
        latitudeRef = gps["GPSLatitudeRef"]
        longitude = gps["GPSLongitude"]
        longitudeRef = gps["GPSLongitudeRef"]
        lat = ConvertToDegrees(latitude)
        lon = ConvertToDegrees(longitude)
        # Check Latitude Reference

        # If South of the Equator then lat value is negative
        if latitudeRef == "S":
            lat = 0 - lat
        # Check Longitude Reference
        # If West of the Prime Meridian in
        # Greenwich then the Longitude value is negative
        if longitudeRef == "W":
            lon = 0- lon
        gpsCoor = {"Lat": lat, "LatRef":latitudeRef, "Lon": lon,"LonRef": longitudeRef}
        return gpsCoor
    else:
        return None

# End ExtractLatLon ===================================
#
# Convert GPSCoordinates to Degrees
#
# Input gpsCoordinates value from in EXIF Format
#

def ConvertToDegrees(gpsCoordinate):
    d0 = gpsCoordinate[0][0]
    d1 = gpsCoordinate[0][1]
    try:
        degrees = float(d0) / float(d1)
    except:
        degrees = 0.0
    m0 = gpsCoordinate[1][0]
    m1 = gpsCoordinate[1][1]
    try:
        minutes = float(m0) / float(m1)
    except:
        minutes=0.0
    s0 = gpsCoordinate[2][0]
    s1 = gpsCoordinate[2][1]
    try:
        seconds = float(s0) / float(s1)
    except:
        seconds = 0.0
    floatCoordinate = float (degrees + (minutes / 60.0) + (seconds /3600.0))
    return floatCoordinate

# End ConvertToDegrees ====================================

import csv #Python Standard Library - reader and writer for csv files
#
# Class: _CSVWriter
#
# Desc: Handles all methods related to comma separated value operations
#
# Methods constructor: Initializes the CSV File
# writeCVSRow: Writes a single row to the csv file
# writerClose: Closes the CSV File

class _CSVWriter:

    def __init__(self, fileName):
        try:
            # create a writer object and then write the header row
            self.csvFile = open(fileName,'wb')
            self.writer = csv.writer(self.csvFile, delimiter=',', quoting=csv.QUOTE_ALL)
            self.writer.writerow( ('Image Path','Make','Model','UTC Time','Lat Ref','Latitude','Lon Ref','Longitude','Alt Ref','Altitude') )
        except:
            logging.error('CSV File Failure')

    def writeCSVRow(self, fileName, cameraMake, cameraModel, utc,latRef, latValue, lonRef, lonValue, altRef, altValue):
        latStr ='%.8f'% latValue
        lonStr='%.8f'% lonValue
        altStr ='%.8f'% altValue
        self.writer.writerow(fileName, cameraMake, cameraModel, utc, latRef, latStr, lonRef, lonStr, altRef, altStr)

    def __del__(self):
        self.csvFile.close()

# End _CSVWrite ==========================================


if __name__ =='__main__':
    main()

    # Program End ========================================================