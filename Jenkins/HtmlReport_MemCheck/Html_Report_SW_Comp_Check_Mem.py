import argparse						#handle parameter
import os           				#Create ouput Folder
import matplotlib.pyplot as pyplot
import matplotlib.cm as colormap	
import numpy						#python numeric
import platform						#OS path handling
import xlrd as excel				#excel handling
import six          				#Indicate variable is string type or not

def parse_args():
    description = "Html Report Generator for Software Component Checking Memory"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-i', '--input-file', dest='inputfile', required=True,
                        help='Input Memory Check excel file need to be put as an argument. It should be the output of calcres_uc.exe')
    parser.add_argument('-o', '--output-path', dest='outputpath', required=True,
                        help='The path of Output folder and html files, [PATH]/Memmory_Check/RAM_SWC.html & ROM_SWC.html')
    parser.add_argument('-dv', '--device', dest='device', required=False,
                        default="Ukn_Device",
                        help='Name of the Device, which will use for naming output files')                    
    return parser.parse_args()

class Summary_Row:
    def __init__(self,Name,ROM_Quota,RAM_Quota):
        self.Name = Name
        self.ROM_Quota = round (float(ROM_Quota),1)
        if(ROM_Quota > 100.0):
            self.ROM_Color_style = "<span style=\"color: #ff0000;\">"
        else:
            self.ROM_Color_style = "<span style=\"color: #339966;\">"
        self.RAM_Quota = round (float(RAM_Quota),1)
        if(RAM_Quota > 100.0):
            self.RAM_Color_style = "<span style=\"color: #ff0000;\">"
        else:
            self.RAM_Color_style = "<span style=\"color: #339966;\">"

class Component_Element:
    def __init__(self,Name,ROM_Budget,ROM_Used,ROM_Percentage,RAM_Budget,RAM_Used,RAM_Precentage):
        self.Name = Name
        self.ROM_Budget = int (ROM_Budget)
        self.ROM_Used = int (ROM_Used)
        self.ROM_Percentage_Used_Budget = float(ROM_Percentage)
        self.RAM_Budget = int (RAM_Budget)
        self.RAM_Used = int (RAM_Used)
        self.RAM_Percentage_Used_Budget = float(RAM_Precentage)
        self.Configure_Status = "Unknown"

if __name__ == '__main__':
    args = parse_args()
    originalDir = os.getcwd()
    Os_Type = platform.system()

    #Create Output Folder
    output_path = args.outputpath
    device_name = args.device
    if not os.path.exists(output_path):
        os.mkdir(output_path)
    
    if Os_Type == "Linux":
        output_path = output_path + "/Memmory_Check/"
    else:
        output_path = output_path + "\\Memmory_Check\\"    
    
    if not os.path.exists(output_path):
        os.mkdir(output_path)

    if Os_Type == "Linux":
        output_path = output_path + "/"+device_name+"/"
    else:
        output_path = output_path + "\\"+device_name+"\\"    
    
    if not os.path.exists(output_path):
        os.mkdir(output_path)

    #Process Input file
    excel_file = args.inputfile
    book = excel.open_workbook(excel_file)
    sheet = book.sheet_by_index(0)
    number_of_row = sheet.nrows
    items = []
    ignored_rows = []
    summary_rows = []
    summary_items = []
    Summary_Index = -1

    #Catching non memory Component row. 
    # e.g:  IF-ADAL	4000	8414 is a memory component
    #       Summary row and label row are not
    for row in range (0,number_of_row):
        #get the lable row (as well as Summary Index Row)
        if isinstance(sheet.cell(row,1).value, six.string_types):
            ignored_rows.append(row)
            #Below code for find out Summary Index row
            try:
                Name = str(sheet.cell(row,0).value)
                if (Name == ""):
                    #Get empty Row
                    Summary_Index = row
            except ValueError:
                continue
        else:
            if (Summary_Index !=-1):
                ignored_rows.append(row)
                try: 
                    Used_Memory = int(sheet.cell(row,2).value)
                    summary_rows.append(row)
                except ValueError:
                    continue


    for row in range (0,number_of_row):
        if (row not in ignored_rows):
            items.append(Component_Element(str(sheet.cell(row,0).value),sheet.cell(row,1).value,sheet.cell(row,2).value,
                                                float(str(sheet.cell(row,3).value).replace(',','.')),sheet.cell(row,5).value,sheet.cell(row,6).value,
                                                float(str(sheet.cell(row,7).value).replace(',','.'))))
        if (row in summary_rows):
            Name = str(sheet.cell(row,0).value)
            summary_items.append(Summary_Row(Name,float(str(sheet.cell(row,3).value).replace(',','.')),float(str(sheet.cell(row,7).value).replace(',','.'))))
    items.reverse()

    RAM_Bar_Name = []
    RAM_Bar_Value = []
    RAM_Bar_Color = []
    RAM_String_Color = []
    ROM_Bar_Name = []
    ROM_Bar_Value = []
    ROM_Bar_Color = []    
    ROM_String_Color = []

    #   Checking the bad input of SW component
    #   If the configuration for planning is too less than Actual (500%):
    #   - show the message in the report.
    #       + bad configure
    #       + no configure
    #   - not draw in the graph.

    for item in items:
        if ((item.RAM_Budget == 1) or (item.ROM_Budget == 1)):
            item.Configure_Status = "No_Conf"
        elif ((item.RAM_Percentage_Used_Budget >= 500.0) or (item.ROM_Percentage_Used_Budget >= 500.0)):
                item.Configure_Status = "Bad"
        else:
            item.Configure_Status = "Good"
            RAM_Bar_Name.append(item.Name)
            RAM_Bar_Value.append(item.RAM_Percentage_Used_Budget)
            ROM_Bar_Name.append(item.Name)
            ROM_Bar_Value.append(item.ROM_Percentage_Used_Budget)
            if (item.RAM_Percentage_Used_Budget <= 100.0):
                RAM_Bar_Color.append("g")
            else:
                RAM_Bar_Color.append("r")
            if (item.ROM_Percentage_Used_Budget <= 100.0):
                ROM_Bar_Color.append("g")
            else:
                ROM_Bar_Color.append("r")    

    #Move to output directory
    os.chdir(output_path)

    #   Plot bar chart with threshold 100% for Budget memory
    #   If Used is more than Budget, make it RED

    #   RAM plotting for SWC Configuration

    #   ROM plotting for SWC Configuration

    #   RAM plotting for SWC
    pyplot.rcdefaults()
    fig, ax = pyplot.subplots()
    RAM_ind = numpy.arange(len(RAM_Bar_Name))
    width = 0.75
    ax.barh(RAM_ind, RAM_Bar_Value, width, color=RAM_Bar_Color)
    pyplot.yticks(RAM_ind, (RAM_Bar_Name))
    pyplot.xticks(numpy.arange(0,max(RAM_Bar_Value)+50,20))
    pyplot.title("SW Component RAM Used per Budget Status", fontweight='bold')
    for ind, value in enumerate (RAM_Bar_Value):
        ax.text(value,ind," "+str(round(value,1))+"%",color = RAM_Bar_Color[ind], va='center')

    fig.savefig("RAM_Used_Budget_SW_Comps.png",bbox_inches='tight')

    #   ROM plotting for SWC
    pyplot.rcdefaults()
    fig, ax = pyplot.subplots()
    ROM_ind = numpy.arange(len(ROM_Bar_Name))
    width = 0.75
    ax.barh(ROM_ind, ROM_Bar_Value, width, color=ROM_Bar_Color)
    pyplot.yticks(ROM_ind, (ROM_Bar_Name))
    pyplot.xticks(numpy.arange(0,max(ROM_Bar_Value)+50,20))
    pyplot.title("SW Component ROM Used per Budget Status", fontweight='bold')
    for ind, value in enumerate (ROM_Bar_Value):
        ax.text(value,ind," "+str(round(value,1))+"%",color = ROM_Bar_Color[ind], va='center')

    fig.savefig("ROM_Used_Budget_SW_Comps.png",bbox_inches='tight')

    #Making html here
    warning_str = ""
    with open("SWC_Memory_Report_Status.html", "w+") as Report_output:
        Report_output.write ("<p style=\"text-align: left;\"><img src=\"ROM_Used_Budget_SW_Comps.png\" alt=\"\" />   <img src=\"RAM_Used_Budget_SW_Comps.png\" alt=\"\" /></p>")
        if(next((i for i, item in enumerate(items) if item.Configure_Status != "Good"), -1) != -1):
            Report_output.write ("<h4 style=\"text-align: Left;\">Below Components need to be checked for Configuration:</h4>")
            for item in items:
                if (item.Configure_Status != "Good"):
                    warning_str = item.Name + " , " + warning_str 
        Report_output.write ("<p style=\"text-align: left;\">" + warning_str + "</p>")
        Report_output.write ("<h4 style=\"text-align: left;\">Overall Status of SWC: </h4>")
        Report_output.write ("<p style=\"text-align: left;\">Global Budget Per Available Memory:</p>")
        Report_output.write ("<p>"+summary_items[0].ROM_Color_style +"ROM: "+ str(summary_items[0].ROM_Quota)+"%,</p>")
        Report_output.write ("<p>"+summary_items[0].RAM_Color_style +"RAM: "+ str(summary_items[0].RAM_Quota)+"%</p>")
        Report_output.write ("<p style=\"text-align: left;\">Used Memory Per Available Memory:</p>")
        Report_output.write ("<p>"+summary_items[1].ROM_Color_style +"ROM: "+ str(summary_items[1].ROM_Quota)+"%,</p>")
        Report_output.write ("<p>"+summary_items[1].RAM_Color_style +"RAM: "+ str(summary_items[1].RAM_Quota)+"%</p>")
        Report_output.write ("<p style=\"text-align: left;\">Component Budget Per Global Budget:</p>")
        Report_output.write ("<p>"+summary_items[2].ROM_Color_style +"ROM: "+ str(summary_items[2].ROM_Quota)+"%,</p>")
        Report_output.write ("<p>"+summary_items[2].RAM_Color_style +"RAM: "+ str(summary_items[2].RAM_Quota)+"%</p>")
        Report_output.write ("<p style=\"text-align: left;\">Used Memory Per Global Budget:</p>")
        Report_output.write ("<p>"+summary_items[3].ROM_Color_style +"ROM: "+ str(summary_items[3].ROM_Quota)+"%,</p>")
        Report_output.write ("<p>"+summary_items[3].RAM_Color_style +"RAM: "+ str(summary_items[3].RAM_Quota)+"%</p>")
    #Change back to current directory
    os.chdir(originalDir)