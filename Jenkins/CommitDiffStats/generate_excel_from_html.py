from bs4 import BeautifulSoup
import xlsxwriter
import argparse
import os


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input-file', required=True,
                        help='Input html file for exporting to excel')
    return parser.parse_args()

def get_table_data(table_id):
    output_rows = []
    tickets_table = soup.find("table", id=table_id)
    for table_row in tickets_table.find_all('tr'):
        columns = table_row.find_all('td')
        output_row = []
        for column in columns:
            if column.text !='' and column.text != 'Create Jira issue':
                output_row.append(column.text)
        output_rows.append(output_row)
    output_rows = list(filter(None, output_rows))
    return output_rows

def create_excel_sheet(data_rows, sheet_name, workbook):
    sheet = workbook.add_worksheet(sheet_name)
    row_length = len(data_rows[0]) - 1
    # Check and remove empty column when create table
    column_length = len(data_rows)
    to = xlsxwriter.utility.xl_col_to_name(row_length) + str(column_length)

    # Find largest string length and resize column
    for i in range(len(data_rows[0])):
        max_len = 0
        try:
            for j in range(column_length-1):
                if max_len < len(data_rows[j][i]):
                    max_len = len(data_rows[j][i])
            sheet.set_column(i, i, max_len+1)
        except IndexError:
            sheet.set_column(i, i, max_len+1)

    header = []
    for i in data_rows[0]:
        header.append({'header': i})
    data_rows.pop(0)
    sheet.add_table(f'A1:{to}', {'data': data_rows, 'columns': header})


if __name__ == '__main__':
    args = parse_args()
    report_name = os.path.splitext(os.path.basename(args.input_file))[0] + ".xlsx"

    if os.path.exists(report_name):
        os.remove(report_name)
        print(f"Removed {report_name}")
    else:
        print(f"Can not delete the file {report_name} as it doesn't exists")

    soup = BeautifulSoup(open(args.input_file), "html.parser")
    ticket_rows = [["Epic", "Ticket", "Ticket type", "Summary", "Assignee", "Fix Version", "Repository", "Status", "Resolution", "Release notes"]]
    file_rows = [["Files", "Changed Type"]]
    header_info = [[soup.find('h1', id='title').get_text()]]

    header_info.append([soup.find('h4', id='repoUrl').get_text()])
    header_info.append([soup.find('h4', id='regex').get_text()])
    header_info.append([soup.find('h4', id='submodules').get_text()])
    header_info.append([soup.find('h4', id='merges').get_text()])

    ticket_rows += get_table_data("tickets")
    file_rows += get_table_data("files")
    workbook = xlsxwriter.Workbook(report_name)
    create_excel_sheet(header_info, "Commits Info", workbook)
    create_excel_sheet(ticket_rows, "Ticket List", workbook)
    create_excel_sheet(file_rows, "Changed Files", workbook)
    workbook.close()
