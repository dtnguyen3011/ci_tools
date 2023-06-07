import argparse
import os
from datetime import datetime
import csv


SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
LICENSE_WARNING = '''Working (fixing and triaging issues) with information
 in this report is only allowed with a QAFramework license !!!
 Otherwise a license violation is committed.
 Using the information for Metric only purposes is fine.'''

_HTML_STYLE = '''
html, body{
    width:98%; 
    background: white; 
    font-family: "Consolas", "Bitstream Vera Sans Mono", monospace !important;
}
table.report {
  font-family: "Times New Roman", Times, monospace;
  text-align: right;
  table-layout: fixed;
  margin-left: 2%; 
  margin-right: 2%;
  width: 98%;
}
table.report td, table.report th {
  border: 1px solid #FFFFFF;
  padding: 2px 2px;
  overflow: hidden; 
  text-overflow: ellipsis; 
  word-wrap: break-word;
}
table.report tr:nth-child(even) {
  background: #E0E4F5;
}
table.report thead {
  background: #06FA4;
}
table.report thead th {
  font-weight: bold;
  color: #FFFFFF;
  text-align: center;
  border-left: 2px solid #FFFFFF;
}
table.report thead th:first-child {
  border-left: none;
}
table.report tfoot {
  font-weight: bold;
  color: #333333;
  background: #E0E4F5;
  border-top: 3px solid #444444;
}
'''

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input-csv', required=True,
                        help='input qacpp analyze csv result file')
    parser.add_argument('-cf', '--changed-files', required=True,
                        help='file contains all changed files in pull request')
    parser.add_argument('-d', '--delimiter', required=True,
                        help='delimiter for csv column')
    parser.add_argument('-id', '--commit-id', default=" ",
                        help='commit id that run input qacpp report')
    parser.add_argument('-ch', '--column-header', default=" ", required=True,
                        help='table column header for html report')
    parser.add_argument('-o', '--output-path',
                        help='output path for generated html file, default is script location')
    return parser.parse_args()

def get_changed_file(file_path):
    with open(file_path, "r") as f:
        changed_files = f.read().splitlines() 
        changed_files = [ i for i in changed_files if i.endswith(".cpp") or i.endswith(".hpp") or i.endswith(".c") or i.endswith(".h")]
    return changed_files

def get_csv_data(file_path, delimiter):
    with open(file_path, "r") as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=f"{delimiter}")
        warning_report = list(csv_reader)
    return warning_report

def create_table_from_list_of_lists(list_of_lists):
    yield '<table class=\"report\">'
    for row in list_of_lists:
        yield '  <tr><td>'
        yield '    </td><td>'.join([str(value) for value in row])
        yield '  </td></tr>'
    yield '</table>'

def create_report_header(title, git_commit, report_description: str):
    return '\n'.join([
        '<h1>Report {}</h1>', '<p><b>{}</b></p>', '<p><b>Date: </b>{}</p>',
        '<p><b>Git Commit: </b>{}</p>'
    ]).format(title, report_description,
              datetime.now().strftime('%d/%m/%Y %H:%M:%S'), git_commit)

def generate_html_report(changed_files, warning_report, git_commit, output_path, column_header):
    changed_files_report = [column_header]
    for i in warning_report:
        for k in changed_files:
            if i[0].replace("\\", "/") in k.replace("\\", "/"):
                changed_files_report.append(i)

    title = "- QACPP only on changed files"
    html_table = '\n'.join(create_table_from_list_of_lists(changed_files_report))
    html_table_style = '<style>\n{}\n</style>'.format(_HTML_STYLE)
    title_style = '<title>{}</title>'.format(title)
    report_header = create_report_header(title, git_commit, LICENSE_WARNING)
    content = '\n'.join([
        '<!DOCTYPE html>', '<html>', '<head>', title_style, html_table_style,
        '</head>', '<body>', report_header, html_table, '</body>', '</html>'
    ])

    html_filepath = args.output_path if args.output_path else SCRIPT_PATH
    html_filepath = os.path.join(html_filepath, "QACPP-report-on-changed-files.html")
    with open(html_filepath, 'w+', newline='', encoding='utf-8') as html_file:
        html_file.write(content)


if __name__ == "__main__":
    args = parse_args()
    column_header = args.column_header.split()
    change_file_list = get_changed_file(args.changed_files)
    report = get_csv_data(args.input_csv, args.delimiter)
    generate_html_report(change_file_list, report, args.commit_id, args.output_path, column_header)
