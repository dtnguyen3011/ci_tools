# Helix helper

This folder contains the project specific implementations and configurations coding rules guidelines from Bosch.

The general EPG workflow you can see here: <br>
[ProLib Actions Standard Activity: Perform Static Code Analysis of SW Units](http://abt-prolib.de.bosch.com:8080/pkit/go/process/element.do?elementType=Activity&elementName=Product+Engineering%7CTest%7CSW+Unit+Verification+%28SW_UVE%29%7CPerform+Static+Code+Analysis+of+SW+Units&projectName=proCCess+library%7CDAS)

The documentation to the Bosch C++ Coding rules you can find here: <br>
[CPP Ruleset Releases](https://inside-docupedia.bosch.com/confluence/display/daprocess/CPP+Ruleset+Releases)


The Helix specific documentation you can find here (including message descriptions, return codes etc.): <br>
[Helix_QAC_Manual](C:\TCC\Tools\helix_qac\2019.2_WIN64\common\doc-en_US\manual\pdf\Helix_QAC_Manual.pdf)

[QACPP Manual](C:\TCC\Tools\helix_qac\2019.2_WIN64\components\qacpp-4.5.0\doc-en_US\component_manual\pdf\qacpp-manual.pdf) (or in any "component" folder.)


Any question regarding coding rules you can create a ticket here:<br>
[Coding Rules Database & Framework Issue Tracker](https://rb-tracker.bosch.com/tracker/projects/CDF/issues)

# Goal
Assist a developer in working (as efficiently as possible) with the QAC Framework. The batch script helix_helper.bat should provide you the most needed functions in order to work with Helix. Under the hood this batch serves as an entry-point for a more complex python script.


# Usage

- It is possible to just launch the script directly from Windows via double-click
- or via CMD and pass arguments directly (e.g. ./helix_helper.bat 1 2)
- or don't use the script at all and just start and configure Helix yourself

If you start the batch, first you have to select which "target" you want to chose (or the first argument). These targets are configured in a .json file and contain blacklists,whitelists, tool and coding rule configurations for a specific build. 

The second option/argument you have the following options:
1. **"create"** : This option will create a new QAC project for you (based on the "target" build in the .json).
2. **"analyze"** : This option will analyze an existing project (with all files synced in it).
3. **"qaview"** : This option will export results from an existing analysis to a spreadsheet and html.
4. **"gui"** : This option will start the GUI for you and load the selected target configuration.
5. **"list"** : This option will require an existing QAC project and will analyze all files specified in the file "qaf_config/prqa_helper_file_list.txt".
6. **"PR"** : This option will require an existing QAC project (from step 1.) and will analyze files according to the diff with the merge-base of your current branch.
7. **"baseline_create"** : This option will require an existing QAC project (from step 1.). It will do a full analysis and afterwards create a baseline.
8. ~~**"baseline_set"** : This option will require an existing baseline (from step 7.)~~ Obsolete, baselines should be configured in the .json target.
9. **"qavupload"** : This option will upload existing analysis results to QAVerify.


# Intended QAC WORKFLOW
In general workign with QAC should consist of the following stages:

- create a new project 
  - (configure messages, rules, compilers)
- load source files (sync)
  - Build monitor / Build Log
- analyze files

1. Start the script and create a new QAC project
   1.  The default mechanism is that the script uses is to get a buildlog via cmakes compile_commands.json file: it uses the build command configured in the .json for this.
   2.  **Make sure the configured/given BUILD_COMMAND works before you blame helix_helper or QAC in general**
       1. Common pitfalls:
          1. Missing submodules (git submodule update --init --recursive)
          2. Missing TCC dependencies (dc_tools/install_DC_TCC_tools.bat)
          3. scom/flux not working correctly
       2. Check the in the .json configured BUILD_LOG file if it contains reasonable results
2. Start the project and perform your analysis
   1. **When opening the project for the first time you see 0 findings because most likely you didn't run an analysis yet.**
   2. Just analyze the files you are worked on. If you have a lot of time analyze the whole project, that will additionally find data-flow warnings
3. When running the analysis use the filters "prqa_helper_analysis_filter.txt" which can blacklist folders/files for the analysis (not sync!)

**The analysis filter (in the .json) will speed up the analysis but it will suppress any data-flow related issues (so your local results differ from QAVerify).**


# Questions

## Why are my results different than the ones in QAVerify?
The results in QAVerify come from this script with the target Jenkins uploaded to the server.
So if you want to 100% reproduce the issues you need to run this exact target locally.

In the local developer "targets" the "dataflow" option is disabled because it takes a long time. This leads to "Definite: , Possible: etc." warnings only be in QAVerify.

Another difference is usually RCMA. This Recursive Cross Module Analysis scans all files for duplicate includes or other issues. The RCMA scan is only activated when you run a full scan.


If you have any doubts about the results please feel free to contact Jauch Ingo (CC-AD/ESW4), ill happily look into it for you.


# Implementation

### Tool installation
To be able to use Helix you should install it via ISM or TCC.
In general the correct version of the tool should be already in the project configuration, otherwise its possible to run the script under: ip_prqa_qaf/3rdpartytools/tcc_scripts/_install_TCC_tools.bat and select the wanted version.
Otherwise you can just copy it from the network share:

[\\\\abtv1000.de.bosch.com\ito\TCC\Tools\helix_qac]([\\\\abtv1000.de.bosch.com\ito\TCC\Tools\helix_qac](file://abtv1000.de.bosch.com/ito/TCC/Tools/helix_qac))

### Folder ip_prqa_qaf
The folder "ip_prqa_qaf" is not a submodule but a hard copy of the official repository, with tag release_1.5.1.
Only scripts from "ip_prqa_qaf\3rdpartytools" were taken from the develop and modified for project context.

### Folder qaf_config
The folder "qaf_config" contains the configuration scripts.

|Filename|Description|
|-|-|
|find_cpp_3rd_party_prefixes.txt|Blacklist configuration for the find_cpp.py|
|find_cpp_code_dirs.txt|folder whitelist for the find_cpp.py|
|helix_helper.json|Main project configuration for the helix_helper.py|
|helix_helper_file_list.txt|Example file in case the helix_helper.bat "list" option is used.|
|PR_changed_files.txt|placeholder file in case the helix_helper.bat "PR" option is used.|