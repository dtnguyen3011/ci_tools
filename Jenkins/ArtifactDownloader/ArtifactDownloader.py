from tkinter import *
import tkinter.messagebox as tkMessageBox
import tkinter.filedialog as tkFileDialog
import subprocess
import os
import json
import logging
import argparse


class WindowsTool:

    defaultArtifactoryServer = "https://rb-artifactory.bosch.com"
    pathSeparator = "/"
    artefactUrlString = None
    artefactProperties = None
    fileDownload = None
    inputUsername = None
    inputPassword = None
    outputPath = None
    logger = None

    def __init__(self, user, password, url, outpath, files, properties=None):
        # Initialize logger instance
        self.initLogger()        
        self.log('d',"WindowsTool()")

        # Initialize windows form
        self.rootWindow = Tk()
        self.rootWindow.resizable(0, 0)
        self.rootWindow.title("Artifact Downloader")

        # Declare all widget elements
        self.wLabelUsername = Label(self.rootWindow)
        self.wLabelUsername["text"] = "Username"
        self.wLabelUsername.grid(row=0,column=0,padx=3,pady=3) 

        self.wEntryUsername = Entry(self.rootWindow)
        self.wEntryUsername["bd"] = 3
        self.wEntryUsername["width"] = 50
        self.wEntryUsername.grid(row=0,column=1,padx=3,pady=3)
        if user:
            self.wEntryUsername.delete(0, END)
            self.wEntryUsername.insert(0, user)

        self.wLabelPassword = Label(self.rootWindow)
        self.wLabelPassword["text"] = "Password"
        self.wLabelPassword.grid(row=1,column=0,padx=3,pady=3)

        self.wEntryPassword = Entry(self.rootWindow)
        self.wEntryPassword["bd"] = 3
        self.wEntryPassword["width"] = 50
        self.wEntryPassword["show"] = "*"
        self.wEntryPassword.grid(row=1,column=1,padx=3,pady=3)
        if password:
            self.wEntryPassword.delete(0, END)
            self.wEntryPassword.insert(0, password)

        self.wLabelArtifactory = Label(self.rootWindow)
        self.wLabelArtifactory["text"] = "Artifact URL"
        self.wLabelArtifactory.grid(row=2,column=0,padx=3,pady=3)

        self.wEntryArtifactory = Entry(self.rootWindow)
        self.wEntryArtifactory["bd"] = 3
        self.wEntryArtifactory["width"] = 50
        self.wEntryArtifactory.grid(row=2,column=1,padx=3,pady=3)
        if url:
            self.wEntryArtifactory.delete(0, END)
            self.wEntryArtifactory.insert(0, url)

        self.wLabelOutput = Label(self.rootWindow)
        self.wLabelOutput["text"] = "Output Location"
        self.wLabelOutput.grid(row=3,column=0,padx=3,pady=3)

        self.wEntryOutput = Entry(self.rootWindow)
        self.wEntryOutput["bd"] = 3
        self.wEntryOutput["width"] = 50
        self.wEntryOutput.grid(row=3,column=1,padx=3,pady=3)
        if outpath:
            self.wEntryOutput.delete(0, END)
            self.wEntryOutput.insert(0, outpath)

        self.wLabelFiles = Label(self.rootWindow)
        self.wLabelFiles["text"] = "File(s) to download\ninput 'all' to download all files"
        self.wLabelFiles.grid(row=4,column=0,padx=3,pady=3)

        self.wEntryFiles = Entry(self.rootWindow)
        self.wEntryFiles["bd"] = 3
        self.wEntryFiles["width"] = 50
        self.wEntryFiles.grid(row=4,column=1,padx=3,pady=3)
        if files:
            self.wEntryFiles.delete(0, END)
            self.wEntryFiles.insert(0, files)

        self.wLabelProperties = Label(self.rootWindow)
        self.wLabelProperties["text"] = "Properties"
        self.wLabelProperties.grid(row=5,column=0,padx=3,pady=3)

        self.wEntryProperties = Entry(self.rootWindow)
        self.wEntryProperties["bd"] = 3
        self.wEntryProperties["width"] = 50
        self.wEntryProperties.grid(row=5,column=1,padx=3,pady=3)
        if properties:
            self.wEntryProperties.delete(0, END)
            self.wEntryProperties.insert(0, properties)

        self.wButtonBrowse = Button(self.rootWindow)
        self.wButtonBrowse["bd"] = 3
        self.wButtonBrowse["width"] = 10
        self.wButtonBrowse["text"] = "Browse"
        self.wButtonBrowse["command"] = self.wButtonBrowse_Callback
        self.wButtonBrowse.grid(row=6,column=1,sticky=W,padx=3,pady=3)

        self.wButtonArtifactory = Button(self.rootWindow)
        self.wButtonArtifactory["bd"] = 3
        self.wButtonArtifactory["width"] = 10
        self.wButtonArtifactory["text"] = "Download"
        self.wButtonArtifactory["command"] = self.wButtonArtifactory_Callback
        self.wButtonArtifactory.grid(row=6,column=1,padx=3,pady=3)

        self.wButtonExit = Button(self.rootWindow)
        self.wButtonExit["bd"] = 3
        self.wButtonExit["width"] = 10
        self.wButtonExit["text"] = "Exit"
        self.wButtonExit["command"] = self.wButtonExit_Callback
        self.wButtonExit.grid(row=6,column=1,sticky=E,padx=3,pady=3)

        # Execute the forever loop to keep the GUI running
        self.rootWindow.mainloop()
        self.log('d',"~WindowsTool()")

    def initLogger(self):
        self.logger = logging.getLogger()
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s [%(levelname)-5s] %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG)
    
    def log(self,logType,*logMsg):
        # print(type(logMsg))
        if isinstance(logMsg,str):
            # print("logMsg is a string")
            msgFull = ' '.join(logMsg)
        else:
            # print("logMsg is NOT a string")
            msgFull = str(logMsg)
        # msgFull = ' '.join(logMsg)
        if logType == 'd': self.logger.debug(msgFull)
        elif logType == 'i': self.logger.info(msgFull)
        elif logType == 'e': self.logger.error(msgFull)
        elif logType == 'w': self.logger.warning(msgFull)
        elif logType == 'c': self.logger.critical(msgFull)
        else: print("[UNKNOWN LOG MODE]")

    def wButtonBrowse_Callback(self):
        self.log('d',"wButtonBrowse_Callback()")
        outputPath = tkFileDialog.askdirectory()
        self.wEntryOutput.delete(0,END)
        self.wEntryOutput.insert(0,outputPath)
        self.log('i',"Selected path: ",outputPath)
        self.log('d',"~wButtonBrowse_Callback()")

    def wButtonExit_Callback(self):
        self.log('d',"wButtonExit_Callback()")
        self.rootWindow.destroy()
        self.log('d',"~wButtonExit_Callback()")

    def wButtonArtifactory_Callback(self):
        self.log('d',"wButtonArtifactory_Callback()")

        ##### DEVELOPMENT MODE #####
        self.inputUsername = self.wEntryUsername.get() if self.wEntryUsername.get() else self.inputUsername
        self.inputPassword = self.wEntryPassword.get() if self.wEntryPassword.get() else self.inputPassword
        self.artefactUrlString = self.wEntryArtifactory.get() if self.wEntryArtifactory.get() else self.artefactUrlString
        self.artefactProperties = self.wEntryProperties.get() if self.wEntryProperties.get() else self.artefactProperties
        self.outputPath = self.wEntryOutput.get() if self.wEntryOutput.get() else self.outputPath       
        self.fileDownload = self.wEntryFiles.get() if self.wEntryFiles.get() else self.fileDownload

        ##### NORMAL MODE #####
        userName = self.wEntryUsername.get()
        passWord = self.wEntryPassword.get()
        artifactoryUrl = self.wEntryArtifactory.get()
        artifactoryProperties = self.wEntryProperties.get()
        outputPath = self.wEntryOutput.get()
        fileDownload = self.wEntryFiles.get()

        if not userName or not passWord or not artifactoryUrl or not outputPath or not fileDownload: 
            tkMessageBox.showinfo("Error","Please input all the information !")
            return

        if not artifactoryProperties:
            artifactoryProperties = ''

        if not os.path.exists(outputPath):
            tkMessageBox.showinfo("Error","Output path does not exist !")
            return

        self.inputUsername = userName
        self.inputPassword = passWord
        self.artefactUrlString = artifactoryUrl
        self.artefactProperties = artifactoryProperties
        self.outputPath = outputPath
        self.fileDownload = fileDownload

        prefix = ''
        # Validate Artifactory URL
        validUrl = self.normalizeArtifactoryPath(self.artefactUrlString)
        if validUrl:
            self.log('i',"URL is okay:",self.pathSeparator.join(validUrl))

            artifactList = self.downloadArtifactsFromRepo(validUrl)    
            if artifactList:
                # Build command to get SW version
                for artifact in artifactList.keys():
                    artifactPropertiesQuery = self.processError(self.executeCurl(self.commandBuildCurl(
                                                                    cmdType="query", 
                                                                    curlUsername=self.inputUsername, 
                                                                    curlPassword=self.inputPassword,
                                                                    queryOption="properties",
                                                                    artifactoryUrl=self.pathSeparator.join(validUrl)+artifact) ) )
                    
                    if not prefix:
                        for i in self.artefactProperties.split(", "):
                            try:
                                prefix = prefix + "_" + artifactPropertiesQuery["data"]["properties"][i][0]
                            except KeyError as ex:
                                self.log('w',"Property '%s' does not exist in artifact '%s'" % (ex, artifact))
                    else:
                        break

                # Add SW version as prefix to artifacts
                for artifact in artifactList.keys():
                    if self.addPrefixToFiles(artifactList[artifact], prefix):
                        self.log('i'," Adding prefix successful for '%s'" % artifact)
                    else:
                        self.log('i'," Adding prefix failed for '%s'" % artifact)
            else:
                self.log('e',"Could not download artifacts !")
        else:
            self.log('w',"URL is not okay")
            # tkMessageBox.showinfo("Warning","URL is invalid !")
        self.log('d',"~wButtonArtifactory_Callback()")

    def executeCurl(self, curlCommandData):
        self.log('d',"executeCurl()")
        curlCommand = ' '.join(curlCommandData['cmd'])
        outputData = {'type':None,'data':None}
        outputProcess = subprocess.Popen(curlCommand, 
                                stdout=subprocess.PIPE, 
                                stderr=subprocess.STDOUT)
        stdout,stderr = outputProcess.communicate()
        if curlCommandData['type'] == 'download':
            outputData['data'] = curlCommandData['cmd'][-1]
            outputData['type'] = 'file'
        elif curlCommandData['type'] == 'query':
            outputData['type'] = 'json'
            try:
                # binary to string
                jsonResult = '%s' % self.processJsonData(stdout.decode("utf-8"))
                jsonOutput = json.loads(jsonResult)
                outputData['data'] = jsonOutput
            except:
                outputData['data'] = {u'errors' : [{u'message':u'No JSON object found'}]} 
                self.log('i'," No JSON object could be decoded")
        else:
            # Type 'reserved' will have data 'None'
            outputData['type'] = 'reserved'

        self.log('d',"~executeCurl()")
        return outputData

    def processJsonData(self, inputData):
        self.log('d',"processJsonData()")
        bufferData = ''
        blockProcess = 0

        for char in inputData:
            if char == '{': 
                blockProcess += 1
            else: 
                if char == '}': 
                    blockProcess -= 1
            
            if blockProcess == 0:
                continue
            else:
                bufferData += char
        # In case the last character is a closed bracket '}', 
        # it will be disregarded, so re-added it.
        if bufferData: bufferData += '}'
        self.log('d',"~processJsonData()")
        return bufferData

    def addPrefixToFiles(self, fileName, namePrefix):
        self.log('d',"addPrefixToFiles()")
        retStatus = False
        # Only consider '.zip' file
        if fileName.endswith(".zip"):
            try:
                fileNameData = fileName.split(self.pathSeparator)
                if len(fileNameData) > 1:
                    fileNameData[-1] = namePrefix + "_" + fileNameData[-1]
                    newFileName = self.pathSeparator.join(fileNameData)
                else:
                    newFileName = namePrefix + "_" + fileName
                    
                self.log('d',"fileName:",fileName)
                self.log('d',"newFileName:",newFileName)
                os.rename(fileName,newFileName) 
                retStatus = True
            except Exception as ex:
                self.log('w',"Could not rename file '%s' because exception '%s' !" % (fileName,ex))
        else:
            self.log('i'," Input file is not 'zip' file !")

        return retStatus
        self.log('d',"~addPrefixToFiles()")

    def normalizeArtifactoryPath(self, inputUrl):
        self.log('d',"normalizeArtifactoryPath()")
        # This func is used for normalizing Artifactory path based on input  
        # URL then validate it. The input URL might come from these 4 scenarios:
        #   1. showing from build job                            -> https://rb-artifactory.bosch.com/artifactory/list/<repository_path>
        #   2. copy from Artifactory repository full file path   -> https://rb-artifactory.bosch.com:443/artifactory/<repository_path>
        #   3. already correct path with "api/storage/"          -> https://rb-artifactory.bosch.com/artifactory/api/storage/<repository_path>
        #   4. copy from Artifactory repository path only        -> <repository_path>

        processingUrl = []
        # Normalize the path separator
        inputUrl = inputUrl.replace('\\',self.pathSeparator)
        # Case 1 & 2 & 3
        if inputUrl.startswith(self.defaultArtifactoryServer):
            testStr = inputUrl.replace(self.defaultArtifactoryServer,"")

            processingUrl = inputUrl.replace(self.defaultArtifactoryServer,"").split(self.pathSeparator)

            if not processingUrl[0]: processingUrl.pop(0) 
            # If the URL contains port info
            if processingUrl[0].startswith(":"): processingUrl.pop(0)            
            if processingUrl[0] == "artifactory": processingUrl.pop(0)
            if processingUrl[0] == "list": processingUrl.pop(0)
            if processingUrl[0] == "api": processingUrl.pop(0)
            if processingUrl[0] == "storage": processingUrl.pop(0)

        processingUrl.insert(0,self.defaultArtifactoryServer + "/artifactory")
        processedUrl = processingUrl[:]
        processingUrl = self.buildArtifactoryRest(processingUrl,"api/storage")

        # Validate:
        if None is self.processError(self.executeCurl(self.commandBuildCurl(cmdType="query", 
                                                            curlUsername=self.inputUsername, 
                                                            curlPassword=self.inputPassword,
                                                            artifactoryUrl=self.pathSeparator.join(processingUrl)) ) ):

            processedUrl = None

        self.log('d',"~normalizeArtifactoryPath()")
        return processedUrl

    def buildArtifactoryRest(self,cmdData,apiPattern):
        self.log('d',"buildArtifactoryRest()")
        cmdData.insert(1, apiPattern)
        self.log('d',"~buildArtifactoryRest()")
        return cmdData

    def commandBuildCurl(self,cmdType,curlUsername,curlPassword,artifactoryUrl,queryOption=None,fullFileName=None):
        self.log('d',"commandBuildCurl()")
        retData = {'type':None, 'cmd':None}
        outputCommand = ["curl"]
        outputCommand.append("-u")
        credentialString = "%s:%s" % (curlUsername,curlPassword)
        outputCommand.append(credentialString) 
        outputCommand.append("-X")
        self.log('d', f"---{cmdType}-----{queryOption}")

        if cmdType == "query":
            outputCommand.append("GET")
            urlString = ''
            if queryOption == "properties": 
                urlString = "\"%s%s\"" % (artifactoryUrl,"?properties")
            else:
                urlString = "\"%s\"" % artifactoryUrl
            outputCommand.append(urlString)
        elif cmdType == "download":
            if fullFileName:
                outputCommand.append("GET")
                urlString = "\"%s\"" % artifactoryUrl
                outputCommand.append(urlString)
                outputCommand.append("--output")
                fullFileName = fullFileName.replace('\\',self.pathSeparator)
                outputCommand.append(fullFileName)
            else:
                raise SyntaxError("'fullFileName' option should be specified for 'download' command type.")
        else:
            # Reserved case, do nothing right now
            outputCommand.append("GET")
            outputCommand.append("\"%s\"") % artifactoryUrl

        retData['type'] = cmdType
        retData['cmd'] = outputCommand
        self.log('d',"~commandBuildCurl()")
        return retData

    def downloadArtifactsFromRepo(self,repoUrlData):
        self.log('d',"downloadArtifactsFromRepo()")
        artifactList = {}
        self.log('i'," repoUrlData",self.pathSeparator.join(repoUrlData))
        repoUrlDataWithApi = repoUrlData[:]
        repoUrlDataWithApi = self.buildArtifactoryRest(repoUrlDataWithApi, "api/storage")
        self.log('i'," repoUrlDataWithApi",repoUrlDataWithApi)        
        curlResult = self.processError(self.executeCurl(self.commandBuildCurl(
                                            cmdType="query", 
                                            curlUsername=self.inputUsername, 
                                            curlPassword=self.inputPassword,
                                            artifactoryUrl=self.pathSeparator.join(repoUrlDataWithApi)) ) )
        
        fileList = self.fileDownload.split(", ")
        if "all" in fileList:
            fileList = []
            if curlResult is not None:
                try:
                    for item in curlResult['data']['children']:
                        if not item['folder']:
                            fileList.append(item['uri'])
                except KeyError as ex:
                    self.log('e',"Property '%s' does not exist due to cURL output is not as expected !" % ex)
            else:
                self.log('e',"cURL executed with invalid result !")
        else:
            for i in range(len(fileList)):
                fileList[i] = "/" + fileList[i].replace(" ", "")

        # self.log('d',"fileList:",fileList)
        for item in fileList:
            curlResult = self.processError(self.executeCurl(self.commandBuildCurl(
                                                cmdType="download",
                                                curlUsername=self.inputUsername,
                                                curlPassword=self.inputPassword,
                                                artifactoryUrl=self.pathSeparator.join(repoUrlData) + item,
                                                fullFileName=self.outputPath + item)))

            # if (curlResult['type']) and (curlResult['type'] == 'file'):
                # artifactList.append(curlResult['data'])
            try:
                artifactList[item] = curlResult['data']
            except KeyError as ex:
                self.log('e',"Property '%s' does not exist !" % ex)
        return artifactList
        self.log('d',"~downloadArtifactsFromRepo()")

    def processError(self,inputData):
        self.log('d',"processError()")
        retStr = None
        # Handle REST API error return 
        if inputData['type'] == 'json': 
            self.log('d',"inputData['data']:",inputData['data'])
            if "errors" in inputData['data']:
                # inputData is 'errors' data
                try:
                    retStr = inputData['data']['errors'][0]['message']
                except:
                    retStr = "No JSON data found" #"Error in JSON data is not as format." 

        # Handle error for file downloadig
        elif inputData['type'] == 'file': 
            if not os.path.isfile(inputData['data']):
                retStr = "File not exist" #"File '%s' could not be download !" % inputData['data']
        else:
            retStr = "Unsupported command"
        
        if retStr is not None:
            self.log('d',"retStr:",retStr)
            msgBox = None
            if retStr == 'Bad credentials': msgBox = "Username and password are not recognized !"
            elif retStr == 'Not Found': msgBox = "Not found" #TODO: check
            elif retStr == 'Unable to find item': msgBox = "Unable to find item" #TODO: check 
            elif retStr == 'No JSON data found': msgBox = "Could not query the REST API through this Artifactory URL !"
            elif retStr == 'File not exist': msgBox = "File '%s' could not be download !" % inputData['data']
            else: msgBox = "Unknown error for this Artifactory URL"
            
            tkMessageBox.showinfo("Error",msgBox)
            self.log('d',"~processError()")
            return None

        self.log('d',"~processError()")
        return inputData


def parse_args():
    description = "Artifactory downloader"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-i', '--input-file',
                        help='Input config file')
    return parser.parse_args()


############################
#           MAIN           #
############################
if __name__ == "__main__":
    args = parse_args()
    if args.input_file:
        with open(args.input_file, "r") as f:
            raw_data = f.read().splitlines()
        for i in range(len(raw_data)):
            raw_data[i] = raw_data[i].split("=")[1].lstrip()
        mainInstance = WindowsTool(raw_data[0], raw_data[1], raw_data[2], raw_data[3], raw_data[4], raw_data[5])
    else:
        mainInstance = WindowsTool(None, None, None, None, None, None)

    mainInstance.log('i',"Module has been executed in standalone mode !")
