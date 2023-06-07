<!---

Copyright (c) 2009, 2019 Robert Bosch GmbH and its subsidiaries.
This program and the accompanying materials are made available under
the terms of the Bosch Internal Open Source License v4
which accompanies this distribution, and is available at
http://bios.intranet.bosch.com/bioslv4.txt

-->

# Helix Helper

This project comprehends a set of scripts aimed to help out projects to create and maintain their own Helix project structures in a flexible and customizable way. This is an alternative to manually configuring the project from commandline.

## Index

  * [About](#about)
  * [Maintainers](#maintainers)
  * [Contributors](#contributors)
  * [License](#license)
  * [How to use it](#use)
  * [How to build and test it](#build)
  * [How to contribute](#contribute)
  * [Used 3rd party Licenses](#licenses)
  * [Used encryption](#encryption)
* [Feedback](#feedback)

## <a name="about">About</a>

  The goal is to have a "standalone" python script that covers all use cases from a project for the Helix framework.
  It utilizes a configuration in JSON format (with comments) that can be adapted to any project.

  1. Add [helix_helper](https://sourcecode.socialcoding.bosch.com/projects/CDF/repos/helix_helper/browse) as submodule of your project or directly add it to your VCS as a tracked file.
  2. [helix_helper.json](#example_json)

  The same script should also be used from Jenkins to have the same reliable configuration and results as a local run.

  Additionally the repo contains another python script:
  - [find_cpps](https://sourcecode.socialcoding.bosch.com/projects/CDF/repos/helix_helper/browse/find_cpps): This one able to determine changed header or inline files and feed the input
  back to the helix_helper.py


## <a name="maintainers">Maintainers</a>

  * [Ingo Jauch](https://connect.bosch.com/profiles/html/profileView.do?key=fccee294-fb86-40cf-8c78-6917f4a69e13)
  * [André Silva](https://connect.bosch.com/profiles/html/profileView.do?key=da1769d2-3f48-4549-962f-5b711cdc45c9)

## <a name="contributors">Contributors</a>

  Consider listing contributors in this section to give explicit credit. You 
  could also ask contributors to add themselves in this file on their own.

## <a name="license">License</a>

  >	Copyright (c) 2009, 2016 Robert Bosch GmbH and its subsidiaries.
  >	This program and the accompanying materials are made available under
  >	the terms of the Bosch Internal Open Source License v4
  >	which accompanies this distribution, and is available at
  >	http://bios.intranet.bosch.com/bioslv4.txt

## <a name="use">How to use it</a>

### helix_helper.json

  Please notice that during the parse step the comments done with '//' are removed so it is possible to keep a commented helix_helper.json file. 


| Key                   | Comment                                                                                                                                                           | Example                                          |
|-----------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------|
| ACF_FILE              | Path relative to project root or absolute to the ACF Helix configuration file                                                                                      | helix/acf/helix_ccda_config_cpp_1.4.acf            |
| ANALYZE_PARAMS        | Customizes analysis parameters to Helix's commands                                                                                                                 | --file-based-analysis --force-complete           |
| BUILD_COMMAND         | Build command that generates a log file, ideally a script, if this field is left empty, no build will be performed                                                | SET DONTBUILD=true & tools\\jenkins\\build.bat   |
| BUILD_LOG             | Either compile_commands.json or the default output of a build log                                                                                                 | build/a_target_dir/compile_commands.json         |
| COMPILER_LIST         | List of CCT files corresponding to the individual used targets                                                                                                    | helix/config/cct/GCC_C++11.cct                    |
| CUSTOM_HELP_PATH      | If specified this path will be replaced in the rcf file to provide custom help message                                                                            | build/armclang_a53_helix                          |
| LOCAL_BASELINE_PATH   | Relative to project root or absolute. If specified, a baseline file will be used (files.sup), helper arg has priority and will override this: helper_set_baseline | build/local_path/                                |
| JSON_FILTER           | File filter to apply as an inclusion mechanism (whitelist)                                                                                                        | .cpp$                                            |
| NCF_FILE              | Path relative to project root or absolute to the NCF Helix configuration file                                                                                      | helix/ncf/helix_ccda_config_cpp_naming_1.0.ncf     |
| PRQA_PROJECT_PATH     | Path relative to project root or absolute, without leadig slash, this will also be the project name                                                               | build/armclang_a53_helix                          |
| PRQA_ANALYSIS_FILTERS | List of Folders to suppress warnings from (-quiet)                                                                                                                | ["build","dc_apl_test","ip_if","ip_mom","rc_fw"] |
| PRQA_MODULES          | Modules are required to apply analysis filters. Only applies if analysis filters are used                                                                         | ["qacpp-4.4.0"]                                  |
| PRQA_SYNC_TYPE        | One of (JSON, BUILD_LOG, MONITOR)                                                                                                                                 | JSON                                             |
| RCF_FILE              | Path relative to project root or absolute to the RCF Helix configuration file                                                                                      | helix/acf/helix_ccda_config_cpp_1.4.rcf            |
| USER_MESSAGES         | Path relative to project root or absolute to the user messages config                                                                                             | helix/user_library/user_messages/messages.xml     |
| VCF_FILE              | Path relative to project root or absolute to the RCF Helix configuration file                                                                                      | helix/acf/helix_ccda_config_git_1.0.xml            |

  Also, please notice that the following configurations can be changed both in the target levels. So information from the outer scope can actually be reused in the target themselves if they are not available there. The hierarchical lookup works:

  1. A value is looked up in the provided commandline arguments;
  2. If not found, then it is looked up in the general configuration file level;
  3. If not found there, then finally it is looked up in the target configuration level.

## <a name="example_json"></a>
  _Example json (filepaths are absolute in this case but could be relative to project_root (commandline defined)_
  ```json
{
    "RCF_FILE": "C:/path_to_proj/config/rcf/helix_ccda_config_cpp_1.4.rcf",
    "ACF_FILE": "C:/path_to_proj/config/acf/helix_ccda_config_cpp_1.2.acf",
    "VCF_FILE": "C:/path_to_proj/config/vcf/helix_ccda_config_git_1.0.xml",

    "test_1_4": {
      "PRQA_PROJECT_PATH": "C:/path_to_proj/helix_project",
      "BUILD_LOG": "samples/bin_gcc/compile_commands.json",
      "PRQA_SYNC_TYPE": "JSON",
      "JSON_FILTER": "\\.cpp$",
      "BUILD_COMMAND": "powershell.exe scripts\\build.ps1 -compiler gcc",
      "ACF_FILE": "C:/path_to_proj/config/acf/helix_ccda_config_cpp_1.4.acf",
      "NCF_FILE": "C:/path_to_proj/config/ncf/helix_ccda_config_cpp_naming_1.0.ncf",
      "USER_MESSAGES": "C:/path_to_proj/config/user_library/user_messages/messages.xml",
      "CUSTOM_HELP_PATH": "",
      "COMPILER_LIST": [
        "C:/path_to_proj/config/cct/GNU_GCC-g++_5.3-x86_64-w64-mingw32-C++-c++11.cct"
      ],
      "ANALYZE_PARAMS": "--file-based-analysis --force-complete -I",
      "PRQA_MODULES": ["qacpp-4.5.0"],
      "PRQA_SYNC_FILTERS": [],
      "PRQA_ANALYSIS_FILTERS": ["build","dc_apl_test","ip_if","ip_vmc","ip_mom","rc_fw"],
      "LOCAL_BASELINE_PATH": ""
    }
}
```

_IF YOU THINK THERE IS A VALUE MISSING PLEASE CONTACT THE MAINTAINERS FIRST BEFORE CHANGING THE SCRIPT_.

### helix_helper.py

Usage is explained in the script help output. Run python helix_helper.py.

The following arguments are available: 

| Argument                              | Comment                                                                                                                                                 | Sources and Type     |
|---------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------|
| -al / --analyse_list                  | Analyzes all files contained in list                                                                                                                    | Arg, Optional        |
| -dp / --datastore_path                | Path to configuration file                                                                                                                              | Arg, Mandatory       |
| -dt / --datastore_target              | Target project to pull configurations from                                                                                                              | Arg, Mandatory       |
| -f / --file                           | Analyzes the given file                                                                                                                                 | Arg, Optional        |
| -hcb / --helper_create_baseline       | If specified, a baseline will be created after an analysis run                                                                                          | Arg,  Optional       |
| -hsb / --helper_set_baseline          | If specified, it will set an baseline when creating a new project from the baseline path                                                                | Arg,  Optional       |
| -hsc / --helper_suppress_c_header     | If set to a yes value all C headers .h will be ignored in the anaylsis                                                                                  | Arg,  Optional       |
| -hsfa / --helper_suppress_file_list_a | Give the absolute path or relative path (relative to project repo folder) of a text file, which contains list of files to be excluded from the analysis | Arg,  Optional       |
| -hsfs / --helper_suppress_file_list_s | Give the absolute path or relative path (relative to project repo folder) of a text file, which contains list of files to be excluded from the sync     | Arg,  Optional       |
| -ht / --helper_target                 | Target command that should be one of ('create', 'analyze', 'report', 'gui', 'qavupload', 'qaview', 's101gen'). Default is 'create'                      | Arg, Optional        |
| -pbs / --build_shell                  | Uses build shel for running a build command                                                                                                             | Arg, File, Optional  |
| -pel / --prqa_error_level             | Set debugging level in prqa to one of ('NONE', 'ERROR', 'INFO', 'DEBUG', 'TRACE'). Default is 'ERROR'                                                   | Arg, File, Optional  |
| -pjb / --project_buildlog_via_arg     | If specified, it uses the following json build log as input to create a prqa project. It will override the build log settings from the config file      | Arg, Optional        |
| -pr / --project_root                  | Path to project relative from the location of the helper script                                                                                         | Arg, File, Optional  |
| -pp / --prqa_path                     | Path to Helix. Default is the latest TCC supported version                                                                                               | Arg, File, Optional  |
| -ppp / --prqa_project_path            | Path to output project                                                                                                                                  | Arg, File, Mandatory |
| -sq / --sonarqube                     | Generate output message and MDR report for SonarQube Plugin                                                                                             | Arg, Optional        |
| -see / --skip_on_error          | If set then will ignore errors and continue execution | Arg, Optional        |
| -vsc / --vscode_integration           | If 'yes', then integrates output into VS-Code                                                                                                           | Arg, Optional        |

### BASELINE WORKFLOW

To properly use the script adhere to the following steps:
1. Create a prqa project with the helper and run an analysis with the arg to create a baseline.
2. Store/share baseline somewhere. I recommend to check it in with the other prqa script configuration.
3. Reference the location of the baseline in the json or pass it as argument when you create a NEW project that you want to analyse against a base line.
4. Run an analyse against a project configured with a baseline.

## <a name="build">How to build and test it</a>

No need to build.
To test if the script works you should once verify the created Helix project in the GUI.

## <a name="contribute">How to contribute</a>

If you want to use this setup or contribute, please first contact the [Maintainers](#maintainers).

## <a name="licenses">Used 3rd party Licenses</a>

None

Software | License
------------------
[Apache Felix](http://felix.apache.org/) | [Apache 2.0 License](http://www.apache.org/licenses/LICENSE-2.0.txt)

## <a name="encryption">Used encryption</a>

Declaration of the usage of any encryption (see BIOS Repository Policy §4.a ).

## <a name="feedback">Feedback</a>

Get in contact with the [Maintainers](#maintainers), e.g. via email or via the [coding rules T&R project](https://rb-tracker.bosch.com/tracker/projects/CDF/summary).

<!---

Copyright (c) 2009, 2019 Robert Bosch GmbH and its subsidiaries.
This program and the accompanying materials are made available under
the terms of the Bosch Internal Open Source License v4
which accompanies this distribution, and is available at
http://bios.intranet.bosch.com/bioslv4.txt

-->
