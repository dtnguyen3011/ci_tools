'''
    File name: Html_Report_Check_Mem.py
    Author: Long Phan Hai (RBVH/ESS6)
    Date created: 13/02/2019
    Date last modified: xx/yy/2019
    Python Version: 2.7 || 3.5
    Library: matplotlib
'''
import re
import argparse
import os           #Create ouput Folder
import matplotlib.pyplot as pyplot
import matplotlib.cm as colormap
import numpy
import platform

def parse_args():
    description = "Html Report Creater for Checking Memory, Output file will create based on input file"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-i', '--input-file', dest='inputfile', required=True,
                        help='Input Memory Check file need to be put as an argument. It should be the output of mem_level_analysis.pl')
    parser.add_argument('-dv', '--device', dest='device', required=False,
                        default="Ukn_Device",
                        help='Name of the Device, which will use for naming output files')
    parser.add_argument('-o', '--output-path', dest='outputpath', required=True,
                        help='The path of Output folder and html files, [PATH]/Memmory_Check/[device]/RAM.html, ROM.html, table.html')
    parser.add_argument('-t', '--time', help='Creation time of the report table', required=False, default='None')
    parser.add_argument('-c', '--commit', help='Commit id used for generating report', required=False, default='None')
    return parser.parse_args()

class Section_element:
    def __init__(self,Name,Free,Free_percentage,Used,Used_percentage):
        self.Name = Name
        self.Free = int (Free)
        self.Used = int (Used)
        self.Free_percentage = float(Free_percentage)
        self.Used_percentage = float(Used_percentage)
        self.Total = Free + Used
    def Calc_Used_percent(self,Sum_Used):
        return (int(round((self.Used/Sum_Used *10000))))/100.00

class Table_Section_Row:
    def __init__(self,Type,Name,Free,FreePercentage,Used,UsedPercentage):
        self.Line_Start = "<tr>\n"
        if Type == "RAM":
            self.Box_1 = "<td style=\"width: 109px;\"><span style=\"color: #00ff00;\">&nbsp;"+Type+"</span></td>\n"
        elif  Type == "ROM":
            self.Box_1 = "<td style=\"width: 109px;\"><span style=\"color: #0000ff;\">&nbsp;"+Type+"</span></td>\n"
        else:
            Box_1 = "<td style=\"width: 109px;\"><span style=\"color: #ff0000;\">&nbsp;Unknown </td>\n"
        self.Box_2 = "<td style=\"width: 247px;\">&nbsp;"+Name+"</td>\n"
        self.Box_3 = "<td style=\"width: 140px;\" align=\"right\">&nbsp;"+Free+"</td>\n"
        self.Box_4 = "<td style=\"width: 200px;\" align=\"right\">&nbsp;"+FreePercentage+"% </td>\n"
        self.Box_5 = "<td style=\"width: 140px;\" align=\"right\">&nbsp;"+Used+"</td>\n"
        self.Box_6 = "<td style=\"width: 200px;\" align=\"right\">&nbsp;"+UsedPercentage+"% </td>\n"
        self.Line_End = "</tr>\n"

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
    input_file_name = args.inputfile
    with open(input_file_name, "r") as input_file:
        input_str = input_file.read()
        # Check if input file is empty
        if not input_str.strip():
            raise ValueError ("[ERROR] Input file is empty")

    print ("-------------------------")
    print ("-----RAM/ROM report:-----")
    print ("-------------------------")
    print ("")
    print (input_str)
    #Catching memory section. 
    # e.g: 0 DSPR	17542	7.1%	228186	92.9% 
    #   OR PFLS 0	-324114	-19.7%	1962514	119.8%
    get_Section_regex = re.compile(r'(^\w+.*)\t(\-*\d*)\t(\d*.*\%)\t(\d*)\t(\d*.*\%)',re.MULTILINE)
    matches = get_Section_regex.findall(input_str)

    #Collect all the memory session
    Sections = []    
    try:
        for match in matches:
            #Remove all non character in string, except " ","-" and "_"
            match_str_0 = re.sub("[^A-Za-z0-9. _-]+","",str(match[0]))
            match_str_1 = re.sub("[^A-Za-z0-9. _-]+","",str(match[1]))
            match_str_2 = re.sub("[^A-Za-z0-9. _-]+","",str(match[2]))
            match_str_3 = re.sub("[^A-Za-z0-9. _-]+","",str(match[3]))
            match_str_4 = re.sub("[^A-Za-z0-9. _-]+","",str(match[4]))
            Sections.append(Section_element(match_str_0,int(match_str_1),float(match_str_2),int(match_str_3),float(match_str_4)))

        Index_Of_RAM_Sec = next((i for i, x in enumerate(Sections) if x.Name == "SUM RAM"), -1)
        Sum_RAM_Section = Section_element(Sections[Index_Of_RAM_Sec].Name,Sections[Index_Of_RAM_Sec].Free,Sections[Index_Of_RAM_Sec].Free_percentage,Sections[Index_Of_RAM_Sec].Used,Sections[Index_Of_RAM_Sec].Used_percentage)
        
        Index_Of_ROM_Sec = next((i for i, x in enumerate(Sections) if x.Name == "SUM ROM"), -1)
        Sum_ROM_Section = Section_element(Sections[Index_Of_ROM_Sec].Name,Sections[Index_Of_ROM_Sec].Free,Sections[Index_Of_ROM_Sec].Free_percentage,Sections[Index_Of_ROM_Sec].Used,Sections[Index_Of_ROM_Sec].Used_percentage)
    except IndexError:
        # Handle Index error in case could not found any matching
        Index_Of_RAM_Sec = -1
    
    if (Index_Of_RAM_Sec == -1) or (Index_Of_ROM_Sec == -1) or (Index_Of_ROM_Sec == Index_Of_RAM_Sec+1) or (Index_Of_RAM_Sec == Index_Of_ROM_Sec+1):
        #throw error here
        raise ValueError ("Memory Report lacks of information")

    #Check if RAM Section is before ROM Section or not, set offset for index
    if Index_Of_RAM_Sec < Index_Of_ROM_Sec:
        RAM_Section_Offset = 0
        ROM_Section_Offset = Index_Of_RAM_Sec + 1
        Number_RAM_Section = Index_Of_RAM_Sec
        Number_ROM_Section = Index_Of_ROM_Sec - Index_Of_RAM_Sec - 1
    else:
        RAM_Section_Offset = Index_Of_ROM_Sec + 1
        ROM_Section_Offset = 0        
        Number_RAM_Section = Index_Of_RAM_Sec - Index_Of_ROM_Sec - 1 
        Number_ROM_Section = Index_Of_ROM_Sec

    #Move to output directory
    os.chdir(output_path)

    # Plotting for RAM
    RAM_ind = numpy.arange(Number_RAM_Section)
    RAM_Section_Name = []
    RAM_Used = []
    RAM_Used_Bar_chart = []
    RAM_Free = []
    RAM_Free_Bar_chart = []
    RAM_Total = []
    No_Free_RAM = True

    RAM_Pie_Chart_Sub_Name = []
    RAM_Pie_Chart_Sub_Section = []
    RAM_Pie_Chart_Color = []
    RAM_Pie_Chart_Sub_Color = []
    RAM_Total_Bar_Chart = []
    color_list = [colormap.Blues, colormap.Reds, colormap.Greens,colormap.Wistia,
                colormap.Pastel2,colormap.YlOrBr,colormap.Purples,colormap.Greys,
                colormap.Accent,colormap.ocean,colormap.OrRd,colormap.Oranges,colormap.BuGn]
    
    #Raw Value calculation
    for i in range (Number_RAM_Section):
        #Bar Chart
        RAM_Used.append(Sections[i+RAM_Section_Offset].Used)
        RAM_Used_Bar_chart.append(RAM_Used[i]/1024)
        RAM_Free.append(Sections[i+RAM_Section_Offset].Free)
        RAM_Free_Bar_chart.append(RAM_Free[i]/1024)
        RAM_Total.append(Sections[i+RAM_Section_Offset].Total)
        RAM_Total_Bar_Chart.append(RAM_Total[i]/1024)
        RAM_Section_Name.append(Sections[i+RAM_Section_Offset].Name)        
    
        #Donut Chart
        RAM_Pie_Chart_Color.append(color_list[i](0.6))
        RAM_Pie_Chart_Sub_Name.append(Sections[i+RAM_Section_Offset].Name + " Used")
        RAM_Pie_Chart_Sub_Section.append(Sections[i+RAM_Section_Offset].Used)
        RAM_Pie_Chart_Sub_Color.append(color_list[i](0.6))
        RAM_Pie_Chart_Sub_Name.append(Sections[i+RAM_Section_Offset].Name + " Free")
        RAM_Pie_Chart_Sub_Section.append(Sections[i+RAM_Section_Offset].Free)
        RAM_Pie_Chart_Sub_Color.append(colormap.Greys(0.3))
        #Check if any section is not good for drawing
        if (Sections[i+RAM_Section_Offset].Free_percentage < 0):
            No_Free_RAM = False

    #Bar Chart for Free/Used percentage
    width =0.35
    p1 = pyplot.bar(RAM_ind,RAM_Used_Bar_chart,width,bottom = 0,align = 'center')
    p2 = pyplot.bar(RAM_ind,RAM_Free_Bar_chart,width,bottom = RAM_Used_Bar_chart,align = 'center')

    pyplot.ylabel ('RAM Used-Free in KBytes')
    pyplot.title ('RAM Status')
    pyplot.xticks(RAM_ind, (RAM_Section_Name))
    pyplot.yticks(numpy.arange(0,max(RAM_Total_Bar_Chart),50))
    pyplot.legend((p1[0],p2[0]),('Used','Free'),loc = "upper center",bbox_to_anchor=(1, 0, 0.25, 1))
    pyplot.savefig('RAM_Check.png',bbox_inches='tight')    
    pyplot.clf()

    #Donut Chart for Total RAM view
    fig2, ax2 = pyplot.subplots()
    ax2.axis('equal')

    #Input for Legend
    Legend_RAM_Total = list(RAM_Total)
    Legend_RAM_Total.append (0)
    Legend_RAM_Section_Name = list(RAM_Section_Name)
    Legend_RAM_Section_Name.append("Free")
    Legend_RAM_Pie_Chart_Color = list(RAM_Pie_Chart_Color)
    Legend_RAM_Pie_Chart_Color.append(colormap.Greys(0.3))

    #For Legend, draw 1 ring with the same position as Outside Ring, and make legend table base on that.
    #The ring shall be overwritten by Outside Ring, so please dont change the order
    myRAM_legend, _ = ax2.pie(Legend_RAM_Total, radius=1.2, colors= Legend_RAM_Pie_Chart_Color,center = (0,0))
    pyplot.setp( myRAM_legend, width=0.2, edgecolor='white')
    
    #Outside Ring
    mypie, _ = ax2.pie(RAM_Total, radius=1.2, labels=RAM_Section_Name, colors= RAM_Pie_Chart_Color,center = (0,0))
    pyplot.setp( mypie, width=0.2, edgecolor='white')
    #inside Ring
    mypie2, _ = ax2.pie(RAM_Pie_Chart_Sub_Section, radius=1.2-0.2, colors= RAM_Pie_Chart_Sub_Color,center = (0,0))
    pyplot.setp( mypie2, width=0.5, edgecolor='white')
    pyplot.margins(0,0)

    
    pyplot.legend(myRAM_legend,Legend_RAM_Section_Name,bbox_to_anchor=(1, 0, 0.25, 1))
    pyplot.savefig('RAM_Used_Free_Total.png',bbox_inches='tight')
    pyplot.clf()

    # Plotting for ROM
    ROM_ind = numpy.arange(Number_ROM_Section)
    ROM_Section_Name = []
    ROM_Used = []
    ROM_Free = []
    ROM_Total = []
    ROM_Used_Bar_Chart = []
    ROM_Free_Bar_Chart = []
    ROM_Total_Bar_Chart = []
    
    ROM_Pie_Chart_Color = []
    ROM_Pie_Chart_Sub_Name = []
    ROM_Pie_Chart_Sub_Section = []
    ROM_Pie_Chart_Sub_Color = []
    No_Free_ROM = True

    #Raw Value calculation
    for i in range (Number_ROM_Section):
        #Bar Chart
        ROM_Used.append(Sections[i+ROM_Section_Offset].Used)
        ROM_Used_Bar_Chart.append(ROM_Used[i]/1024)
        ROM_Free.append(Sections[i+ROM_Section_Offset].Free)
        ROM_Free_Bar_Chart.append(ROM_Free[i]/1024)
        ROM_Total.append(Sections[i+ROM_Section_Offset].Total)
        ROM_Total_Bar_Chart.append(ROM_Total[i]/1024)
        ROM_Section_Name.append(Sections[i+ROM_Section_Offset].Name)
        #Donut Chart
        ROM_Pie_Chart_Color.append(color_list[i](0.6))
        ROM_Pie_Chart_Sub_Name.append(Sections[i+ROM_Section_Offset].Name + " Used")
        ROM_Pie_Chart_Sub_Section.append(Sections[i+ROM_Section_Offset].Used)
        ROM_Pie_Chart_Sub_Color.append(color_list[i](0.6))
        ROM_Pie_Chart_Sub_Name.append(Sections[i+ROM_Section_Offset].Name + " Free")
        ROM_Pie_Chart_Sub_Section.append(Sections[i+ROM_Section_Offset].Free)
        ROM_Pie_Chart_Sub_Color.append(colormap.Greys(0.3))
        #Check if any section is not good for drawing
        if (Sections[i+ROM_Section_Offset].Free_percentage < 0):
            No_Free_ROM = False

    #Bar Chart for Free/Used percentage
    p1 = pyplot.bar(ROM_ind,ROM_Used_Bar_Chart,width,bottom = 0,align = 'center')
    p2 = pyplot.bar(ROM_ind,ROM_Free_Bar_Chart,width,bottom = ROM_Used_Bar_Chart,align = 'center')

    pyplot.ylabel ('ROM Used-Free in KBytes')
    pyplot.title ('ROM Status')
    pyplot.xticks(ROM_ind, (ROM_Section_Name))
    pyplot.yticks(numpy.arange(0,max(ROM_Total_Bar_Chart),500))
    pyplot.legend((p1[0],p2[0]),('Used','Free'),loc = "upper center",bbox_to_anchor=(1, 0, 0.25, 1))
    pyplot.savefig('ROM_Check.png',bbox_inches='tight')    
    pyplot.clf()

    #Donut Chart for Total ROM view
    fig2, ax2 = pyplot.subplots()
    ax2.axis('equal')

    #Input for Legend
    Legend_ROM_Total = list(ROM_Total)
    Legend_ROM_Total.append (0)
    Legend_ROM_Section_Name = list(ROM_Section_Name)
    Legend_ROM_Section_Name.append("Free")
    Legend_ROM_Pie_Chart_Color = list(ROM_Pie_Chart_Color)
    Legend_ROM_Pie_Chart_Color.append(colormap.Greys(0.3))

    #For Legend, draw 1 ring with the same position as Outside Ring, and make legend table base on that.
    #The ring shall be overwritten by Outside Ring, so please dont change the order
    myROM_legend, _ = ax2.pie(Legend_ROM_Total, radius=1.2, colors= Legend_ROM_Pie_Chart_Color,center = (0,0))
    pyplot.setp( myROM_legend, width=0.2, edgecolor='white')
    #Outside Ring
    mypie, _ = ax2.pie(ROM_Total, radius=1.2, labels=ROM_Section_Name, colors= ROM_Pie_Chart_Color,center = (0,0))
    pyplot.setp( mypie, width=0.2, edgecolor='white')
    #inside Ring
    mypie2, _ = ax2.pie(ROM_Pie_Chart_Sub_Section, radius=1.2-0.2, colors= ROM_Pie_Chart_Sub_Color,center = (0,0))
    pyplot.setp( mypie2, width=0.5, edgecolor='white')
    pyplot.margins(0,0)

    
    pyplot.legend(myROM_legend,Legend_ROM_Section_Name,bbox_to_anchor=(1, 0, 0.25, 1))
    pyplot.savefig('ROM_Used_Free_Total.png',bbox_inches='tight')
    pyplot.clf()

    #Raw calculation for table
    Tables = []
    totalRamUsed = 0
    totalRamFree = 0
    totalRomUsed = 0
    totalRomFree = 0
    for i in range (Number_RAM_Section):
        Tables.append(Table_Section_Row("RAM",Sections[i+RAM_Section_Offset].Name,str(Sections[i+RAM_Section_Offset].Free),
                        str(Sections[i+RAM_Section_Offset].Free_percentage),str(Sections[i+RAM_Section_Offset].Used),str(Sections[i+RAM_Section_Offset].Used_percentage)))
        totalRamUsed += Sections[i+RAM_Section_Offset].Used
        totalRamFree += Sections[i+RAM_Section_Offset].Free
    
    for i in range (Number_ROM_Section):
        Tables.append(Table_Section_Row("ROM",Sections[i+ROM_Section_Offset].Name,str(Sections[i+ROM_Section_Offset].Free),
                        str(Sections[i+ROM_Section_Offset].Free_percentage),str(Sections[i+ROM_Section_Offset].Used),str(Sections[i+ROM_Section_Offset].Used_percentage)))
        totalRomUsed += Sections[i+ROM_Section_Offset].Used
        totalRomFree += Sections[i+ROM_Section_Offset].Free

    #Making Table for Report
    with open("table.html", "w+") as Memory_table:
        Memory_table.write  (f"<h1><span style=\"color: #0000ff;\"><strong>RAM ROM Report Table on {args.commit} at {args.time}<br /></strong></span></h1>\n")
        Memory_table.write ("<table style=\"height: 210px; width: 476px; float: left;\">\n")
        Memory_table.write ("<thead>\n")
        Memory_table.write ("<tr>\n")
        Memory_table.write ("<th style=\"width: 109px;\">&nbsp;<strong>RAM/ROM</strong></th>\n")
        Memory_table.write ("<th style=\"width: 247px;\">&nbsp;<strong>Section Name</strong></th>\n")
        Memory_table.write ("<th style=\"width: 140px;\"><strong>Free in Byte<br /></strong></th>\n")
        Memory_table.write ("<th style=\"width: 200px;\"><strong>Free Percentage<br /></strong></th>\n")
        Memory_table.write ("<th style=\"width: 140px;\"><strong>Used in Byte<br /></strong></th>\n")
        Memory_table.write ("<th style=\"width: 200px;\"><strong>Used Percentage<br /></strong></th>\n")
        Memory_table.write ("</tr>\n")
        Memory_table.write ("</thead>\n")
        Memory_table.write ("<tbody>\n")
        #Writing Table
        for Table in Tables:
            Memory_table.write (Table.Line_Start)
            Memory_table.write (Table.Box_1)
            Memory_table.write (Table.Box_2)
            Memory_table.write (Table.Box_3)
            Memory_table.write (Table.Box_4)
            Memory_table.write (Table.Box_5)
            Memory_table.write (Table.Box_6)
            Memory_table.write (Table.Line_End)
        Memory_table.write ("</tbody>\n")
        Memory_table.write ("<tfoot>\n")
        Memory_table.write ("<tr>\n")
        Memory_table.write ("<tr><td colspan=\"6\"><hr /></td></tr>\n")
        Memory_table.write ("<td><span style=\"color: #00ff00;\">&nbsp;RAM</span></td>\n")
        Memory_table.write ("<td>TOTAL</td>\n")
        Memory_table.write ("<td align=\"right\">" + str(totalRamFree) + "</td>\n")
        Memory_table.write ("<td align=\"right\">" + str(0) + "</td>\n")
        Memory_table.write ("<td align=\"right\">" + str(totalRamUsed) + "</td>\n")
        Memory_table.write ("<td align=\"right\">" + str(0) + "</td>\n")
        Memory_table.write ("</tr>\n")
        Memory_table.write ("<tr>\n")
        Memory_table.write ("<td><span style=\"color: #0000ff;\">&nbsp;ROM</span></td>\n")
        Memory_table.write ("<td>TOTAL</td>\n")
        Memory_table.write ("<td align=\"right\">" + str(totalRomFree) + "</td>\n")
        Memory_table.write ("<td align=\"right\">" + str(0) + "</td>\n")
        Memory_table.write ("<td align=\"right\">" + str(totalRomUsed) + "</td>\n")
        Memory_table.write ("<td align=\"right\">" + str(0) + "</td>\n")
        Memory_table.write ("</tr>\n")
        Memory_table.write ("</tfoot>\n")
        Memory_table.write ("</table>\n")

    #Making html Report
    with open("RAM.html", "w+") as RAM_output:
        RAM_output.write ("<p><img src=\"RAM_Check.png\" alt=\"\" /></p>")
        RAM_output.write ("<p><img src=\"RAM_Used_Free_Total.png\" alt=\"\" /></p>")
        if(No_Free_RAM == False):
            RAM_output.write ("<p>The Input is not good, Section(s) has no Free Space, Graph could be not correct </p>")

    with open("ROM.html", "w+") as ROM_output:        
        ROM_output.write ("<p><img src=\"ROM_Check.png\" alt=\"\" /></p>")
        ROM_output.write ("<p><img src=\"ROM_Used_Free_Total.png\" alt=\"\" /></p>")
        if (No_Free_ROM == False):
            ROM_output.write ("<p>The input is not good, Section(s) has no Free Space, Graph could be not correct </p>")

    #Change back to current directory
    os.chdir(originalDir)