'''
    File name: Statistics_Branch_Number.py
    Author: Long Phan Hai (RBVH/ESS6)
    Date created: 28/02/2019
    Date last modified: 05/04/2019
    Python Version: 2.7 || 3.5
    Library: pymongo 3.7.2
    SSL CA Certificate: https://inside-ws.bosch.com/FIRSTspiritWeb/wcms/wcms_so/media/so/communication_center/documents_1/rb_trustcenter/en/CA_certificates_for_Bosch_internal_SSL_certificates_2.zip
'''

import pymongo
import ssl
import argparse
import subprocess       
from datetime import date
#from datetime import timedelta
import json
import os
import sys

def parse_args():
    description = "MongoDB Update Branch Number Script"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-udb', '--usernamedb', dest='usernamedb', required=True,
                        help='Username for access MongoDB')
    parser.add_argument('-pdb', '--passworddb', dest='passworddb', required=True,
                        help='Password for access MongoDB')        
    parser.add_argument('-ubb', '--usernamebb', dest='usernamebb', required=True,
                        help='Username for access BitBucket')
    parser.add_argument('-pbb', '--passwordbb', dest='passwordbb', required=True,
                        help='Password for access BitBucket')
    parser.add_argument('-pj', '--project', dest='project', required=True,
                        help='Project in BitBucket')
    parser.add_argument('-rp', '--repo', dest='repo', required=True,
                        help='Repository in BitBucket')
    parser.add_argument('-cer', '--CACertificate', dest='CACert', required=False,
                        default="C:/Program Files/MongoDB/Server/4.0/data/BOSCH-CA-DE_pem.cer",
                        help='Absolute path to SSL CA Certificate')  
    parser.add_argument('-host', '--hostname', dest='host', required=False,
                        default='SI0VM02891.de.bosch.com',
                        help="Host name of MongoDB server")
    parser.add_argument('-port', '--portnumber', dest='port', required=False,
                        default=30000,
                        help='port to connect MongoDB server')
    parser.add_argument('-repset', '--replicasetname', dest='replicaset', required=False,
                        default="radar_customer_gen5_rep",
                        help='ReplicasetName for MongoDB server')
    parser.add_argument('-authDB', '--authenticationDatabase', dest='authDB', required=False,
                        default="Jenkins",
                        help='Authentication Database in MongoDB server')
    parser.add_argument('-col', '--collection', dest='collection', required=False,
                        default= "VW_Branch_Statistic",
                        help='Collection name in MongoDB')                                    
    parser.add_argument('-out', '--output-path', dest='outputpath', required=False,
                        default=os.path.dirname(os.path.abspath(
                            sys.argv[0])) + os.sep,
                        help='Output path of the json output file,[PATH]/branch_data.json')
                                      
    return parser.parse_args()

class Branch_Statistic_data:
    def __init__(self,Date,Branch,Data_ID):
        self.Json_Format = {
            'Date': Date,
            'Branch': Branch,
            'Data_ID':Data_ID
        }

if __name__ == '__main__':
    #Handle arguments
    args = parse_args()
    DBUserName = args.usernamedb
    DBPassWord = args.passworddb
    BBUserName = args.usernamebb
    BBPassWord = args.passwordbb
    ProjectName = args.project
    RepositoryName = args.repo
    CA_Cert_file = args.CACert
    host = args.host
    port = int(args.port)
    Database = args.authDB
    replicasetname = args.replicaset
    Collection = args.collection
    output_path = args.outputpath

    Repo_url = 'https://sourcecode01.de.bosch.com/rest/api/1.0/projects/' + ProjectName + '/repos/' + RepositoryName + '/branches'

    originalDir = os.getcwd()

    #Create Output Folder
    if not os.path.exists(output_path):
        try:
            os.mkdir(output_path)
        except ValueError as ve: #cannot create output directory
            raise ValueError ("Cannot Create Output Directory, Message: " +str(ve))
            
    #Move to output directory
    os.chdir(output_path)

    #Data of Time 
    today_str = str(date.today())
    start = 0
    isLastPage = False
    
    while (isLastPage == False):
        #Get the current number of branches by using REST API from BB
        command = 'curl -u '+ BBUserName +':'+ BBPassWord +' '+Repo_url+'?start='+ str(start) +''
        pipe = subprocess.Popen(command,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE) 
        out, err = pipe.communicate()
        jsondata = json.loads(out.decode("utf-8"))
        isLastPage = jsondata['isLastPage']
        if (jsondata['isLastPage'] == False):
            start = jsondata['nextPageStart']
        else:
            NumberOfBranch = jsondata['start']+jsondata['size']

    #Connect to MongoDB server
    client = pymongo.MongoClient(   host=host ,port = port,replicaset=replicasetname,ssl=True,ssl_cert_reqs=ssl.CERT_REQUIRED,
                                    ssl_ca_certs=CA_Cert_file,username=DBUserName,password=DBPassWord,authSource=Database,authMechanism='SCRAM-SHA-1')
    Branch_Stats_collection = client[Database][Collection]

    #Collect all documents
    #Should have a better filter to find item in MongoDB to reduce used Stored Memory for running script
    Raw_data = Branch_Stats_collection.aggregate([
        { 
            "$sort" : {"Data_id":1}
        },
        {
            "$group":
            {
                "_id": "$_id",
                "branch": { "$first": "$number_of_branches" },
                "date_check":{ "$first": "$date" },
                "Data_id":{"$first": "$Data_id" }
            }
        }
    ])
    #Convert to a list of dict object
    Raw_data = list(Raw_data)
    print ("Current MongoDB branch Stats has " + str(len(Raw_data)) + " Documents")

    data_for_graph = []
    Data_IDs = []
    Data_Dates = []
    Start_point_of_graph = 0
    Data= {"document":[]}

    #Process Raw_data
    """ for x in Raw_data:
        if x['date_check'] == Weekago_str:
            Start_point_of_graph = int(x['Data_id'])
            break """
    
    for x in Raw_data:
        #if int(x['Data_id']) > Start_point_of_graph: #if database less than 7days, wrap all
        data_for_graph.append(Branch_Statistic_data(str(x['date_check']),int(x['branch']),int(x['Data_id'])).Json_Format)
        Data_IDs.append(int(x['Data_id']))
        Data_Dates.append(str(x['date_check']))

    #Remove duplicate Date in Documents
    Data_Dates = list(set(Data_Dates))
    for x in data_for_graph:
        for y in Data_Dates:
            if (x['Date'] == y):
                Data_Dates.remove(y)
                Data['document'].append(x)
                break            

    Push_Data_ID = max(Data_IDs) + 1
    
    #Adding Current Data to graph if today data is not yet available.
    Data_Tobe_Added = Branch_Statistic_data(str(today_str),int(NumberOfBranch),int(Push_Data_ID))
    
    if(next((i for i, x in enumerate(Data['document']) if x['Date'] == today_str), -1) == -1):
        Data['document'].append(Data_Tobe_Added.Json_Format)
        #Push Current Data to MongoDB
        result = Branch_Stats_collection.insert_one({
            'date': Data_Tobe_Added.Json_Format['Date'],
            'number_of_branches': Data_Tobe_Added.Json_Format['Branch'],
            'Data_id': Data_Tobe_Added.Json_Format['Data_ID']
        })
    
    with open('branch_data.json','w') as outputdata:
        json.dump(Data,outputdata)

    #Change back to current directory
    os.chdir(originalDir)