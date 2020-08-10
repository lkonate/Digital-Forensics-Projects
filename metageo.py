
import os
import argparse
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

def CommandLineInterface():
    parser = argparse.ArgumentParser('Python gpsExtractor')
    parser.add_argument('-v','--verbose', help="enables printing of additional program messages", action='store_true')
    parser.add_argument('-c','--csvPath', type= ValidateDirectory, required=True, help="specify the output directory for the csv file")
    parser.add_argument('-d','--scanPath', type= ValidateDirectory, required=True, help="specify the directory to scan")
    args = parser.parse_args()
    return args

def ValidateDirectory(theDir):
    # Validate the path is a directory
    if not os.path.isdir(theDir):
        raise argparse.ArgumentTypeError('Directory does not exist')
    # Validate the path is writable
    if os.access(theDir, os.W_OK):
        return theDir
    else:
        raise argparse.ArgumentTypeError('Directory is not writable')

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

import csv

class CSVWriter:
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

def main():
    # Offsets into the return EXIFData for
    # TimeStamp, Camera Make and Model
    TS = 0
    MAKE = 1
    MODEL = 2
    # Process the Command Line Arguments
    userArgs = CommandLineInterface()
    csvPath = userArgs.csvPath+"imageResults.csv"
    csvOut = CSVWriter(csvPath)
    # define a directory to scan
    scanDir = userArgs.scanPath
    try:
        picList = os.listdir(scanDir)
    except:
        print("ERROR: "+ scanDir + " is an Invalid Directory ")
        exit(0)

    print ("Program Start\n")
    for aFile in picList:
        targetFile = scanDir+aFile
        if os.path.isfile(targetFile):
            gpsDictionary, EXIFList = ExtractGPSDictionary (targetFile)
            if (gpsDictionary):
                # Obtain the Lat Lon values from the gpsDictionary
                # Converted to degrees
                # The return value is a dictionary key value pairs
                dCoor = ExtractLatLon(gpsDictionary)
                lat = dCoor.get("Lat")
                latRef = dCoor.get("LatRef")
                lon = dCoor.get("Lon")
                lonRef = dCoor.get("LonRef")
                if ( lat and lon and latRef and lonRef):
                    print(str(lat)+','+str(lon))
                    # write one row to the output file
                    csvOut.writeCSVRow(targetFile, EXIFList[TS], EXIFList[MAKE], EXIFList[MODEL],latRef, lat, lonRef, lon)
                    print("GPS Data Calculated for :" + targetFile)
                else:
                    print("No GPS EXIF Data for "+ targetFile)
            else:
                print("No GPS EXIF Data for "+ targetFile)
        else:
            print(targetFile + " is not a valid file")
    # Clean up and Close Log and CSV File
    del csvOut

if __name__ =='__main__':
    main()
