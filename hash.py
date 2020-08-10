
import os
import sys
import stat
import time
import hashlib
import argparse
import csv

def CommandLineInterface():
    
    # Desc:
    # Uses the standard library argparse to process the command line
    # establishes a global variable gl_args where any of the functions can
    # obtain argument information
    #
    parser = argparse.ArgumentParser('Python file system hashing ...')
    parser.add_argument('-v','—-verbose', help='allows progress messages to be displayed', action='store_true')
    # setup a group where the selection is mutually exclusive and required.
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--md5', help ='specifies MD5 algorithm', action='store_true')
    group.add_argument('--sha256', help ='specifies SHA256 algorithm', action='store_true')
    group.add_argument('--sha512', help ='specifies SHA512 algorithm', action='store_true')
    parser.add_argument('-d','--rootPath', type= ValidateDirectory, required=True, help="specify the rootpath for hashing")
    parser.add_argument('-r','--reportPath', type= ValidateDirectoryWritable, required=True, help="specify the path for reports ")
    # create a global object to hold the validated arguments
    global gl_args
    global gl_hashType
    
    gl_args = parser.parse_args()

    if gl_args.md5:
        gl_hashType ='MD5'
    elif gl_args.sha256:
        gl_hashType ='SHA256'
    elif gl_args.sha512:
        gl_hashType ='SHA512'
    else:
        gl_hashType = "Unknown"
        print('Unknown Hash Type Specified')
    
    print("Command line processed: Successfully")
    return

def WalkPath():

    # Desc:
    # Uses the standard library modules os and sys
    # to traverse the directory structure starting at root
    # path specified by the user. For each file discovered, it
    # will call the Function HashFile() to perform the file hashing
    #
    processCount = 0
    errorCount = 0
    csvOut = CSVWriter(gl_args.reportPath+'fileSystemReport.csv', gl_hashType)
    # Create a loop that processes all the files starting
    # at the rootPath, all sub-directories will also be processed
    for root, dirs, files in os.walk(gl_args.rootPath):
        # for each file obtain the filename and call the HashFile Function
        for file in files:
            fname = os.path.join(root, file)
            result = HashFile(fname, file, csvOut)
            # if hashing was successful then increment the ProcessCount
            if result is True:
                processCount += 1
            # if not successful, the increment the ErrorCount
            else:
                ErrorCount += 1
    csvOut.writerClose()
    return(processCount)

def HashFile(theFile, simpleName, o_result):
    #
    # Desc:
    # Processes a single file hash and extracts metadata
    # Uses Python Standard Library modules hashlib, os, and sys
    #
    # Inputs:
    # theFile = the full path of the file
    # simpleName = just the filename itself
    # o_result = CSVWriter object for result
    #
    # Verify that the path is valid
    if os.path.exists(theFile):
        #Verify that the path is not a symbolic link
        if not os.path.islink(theFile):
            #Verify that the file is real
            if os.path.isfile(theFile):
                try:
                    #Attempt to open the file
                    f = open(theFile,'rb')
                except IOError:
                    #if open fails report the error
                    print('Open Failed:'+ theFile)
                    return
                else:
                    try:
                        # Attempt to read the file
                        rd = f.read()
                    except IOError:
                        # On failure, close the file and report error
                        f.close()
                        print('Read Failed:'+ theFile)
                        return
                    else:
                        # On read success, obtain the file's stats
                        (mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime) = os.stat(theFile)
                        #Print the simple file name
                        print("Processing File: " + theFile)
                        # print the size of the file in Bytes
                        fileSize = str(size)
                        #print MAC Times
                        fileMode =bin(mode)
                        fileID = ino
                        deviceID = dev
                        fileLinks = nlink
                        ownerID = str(uid)
                        groupID = str(gid)
                        fileSize = str(size)
                        accessTime = time.ctime(atime)
                        modifiedTime = time.ctime(mtime)
                        createdTime = time.ctime(ctime)
                        #process the file hashes
                        if gl_args.md5:
                            #Calcuation and Print the MD5
                            hash = hashlib.md5()
                            hash.update(rd.encode('utf-8'))
                            hashValue = hash.hexdigest()
                        elif gl_args.sha256:
                            hash = hashlib.sha256()
                            hash.update(rd.encode('utf-8'))
                            hashValue = hash.hexdigest()
                        elif gl_args.sha512:
                            #Calculate and Print the SHA512
                            hash = hashlib.sha512()
                            hash.update(rd.encode('utf-8'))
                            hashValue = hash.hexdigest()
                        else:
                            print('Hash Type should be either md5, sha256, or sha512!')
                        #File processing completed
                        #Close the Active File
                        print ("============================")
                        f.close()
                        # write one row to the output file
                        o_result.writeCSVRow(simpleName, theFile, fileSize, modifiedTime, accessTime, createdTime, hashValue, ownerID, groupID, fileMode)
                        return True
            else:
                print(repr(simpleName) +' is NOT a File!')
                return False
        else:
            print(repr(simpleName) +' is a Link NOT a File!')
            return False
    else:
        print(repr(simpleName) +' is NOT an existing Path!')
    return False

def ValidateDirectory(theDir):
    #
    # Desc:
    # Function that will validate a directory path as existing and readable.
    # Used for argument validation only
    #
    # Actions:
    # if valid it will return the Directory String
    # if invalid it will raise an ArgumentTypeError within argparse
    # which will in turn be reported by argparse to the user
    #
    # Validate the path is a directory
    if not os.path.isdir(theDir):
        raise argparse.ArgumentTypeError('Directory does not exist!')
    # Validate the path is readable
    if os.access(theDir, os.R_OK):
        return theDir
    else:
        raise argparse.ArgumentTypeError('Directory is not readable!')

def ValidateDirectoryWritable(theDir):
    #
    # Desc:
    # Function that will validate a directory path as existing and writable.
    # Used for argument validation only
    #
    # Actions:
    # if invalid it will raise an ArgumentTypeError within argparse
    # which will in turn be reported by argparse to the user
    #
    # Validate the path is a directory
    if not os.path.isdir(theDir):
        raise argparse.ArgumentTypeError('Directory does not exist!')
    # Validate the path is writable
    if os.access(theDir, os.W_OK):
        return theDir
    else:
        raise argparse.ArgumentTypeError('Directory is not writable!')

class CSVWriter:
    #
    # Desc:
    # Handles all methods related to comma separated value operations
    #
    # Methods:
    # constructor: Initializes the CSV File
    # writeCSVRow: Writes a single row to the csv file
    # writerClose: Closes the CSV File
    #
    def __init__(self, fileName, hashType):
        try:
            # create a writer object and then write the header row
            self.csvFile = open(fileName,'wb')
            self.writer = csv.writer(self.csvFile, delimiter=',', quoting=csv.QUOTE_ALL)
            # write the header row
            self.writer.writerow( ('File','Path','Size','Modified Time','Access Time','Created Time', hashType,'Owner','Group','Mode'))
        except:
            print('CSV File Failure')
    
    def writeCSVRow(self, fileName, filePath, fileSize, mTime, aTime, cTime, hashVal, own, grp, mod):
        self.writer.writerow( (fileName, filePath, fileSize, mTime, aTime, cTime, hashVal, own, grp, mod))
    
    def writerClose(self):
        self.csvFile.close()


if __name__ =='__main__':
    CommandLineInterface()
    # Record the Starting Time
    startTime = time.time()
    # Record the Welcome Message
    print('Welcome to Python File System Hashing')
    # Traverse the file system directories and hash the files
    filesProcessed = WalkPath()
    # Record the end time and calculate the duration
    endTime = time.time()
    duration = endTime - startTime
    print('Files Processed:'+ str(filesProcessed) )
    print('Elapsed Time:'+ str(duration) +'seconds')
    print("Program End")
