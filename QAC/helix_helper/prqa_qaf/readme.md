# Perforce Helix Configuration

* [About](#about)
* [Maintainers](#maintainers)
* [Subprojects](#subprojects)
* [How to use it](#use)
* [How to contribute](#contribute)
* [Feedback](#feedback)


## <a name="about">About</a>

This repository contains the configuration for Helix local desktop analysis (with Helix GUI or MS Visual Studio / Eclipse Plugin) with the following setup:

* qacpp analysis together with mcpp (misra cpp), certcpp and rcma (cross module analysis)
* ARM Compiler 6 for an ARMv8 A53 target
* ARM Compiler 6 for an ARMv7 R7 target
* ARM Compiler 6 for an ARMv7 R5 target
* GHS Compiler 201715 for a Tricore/Aurix target
* GHS Compiler 201815 for a Tricore/Aurix target
* GHS Compiler 201713 for a RH850 target
* GHS Compiler 201815 for a RH850 target
* CC-DA EPG C++ Codingrules
* CC-DA Git configuration for SocialCoding/BIOS Bitbucket
* CC-DA C++ Namingrules check


## <a name="maintainers">Maintainers</a>

* [Thomas Jäger](https://connect.bosch.com/profiles/html/profileView.do?key=f04f7c59-5eef-4de2-acc9-e00178affb41)


## <a name="subprojects">Subprojects</a>

The [Helix helper](3rdpartytools/readme.md) is a helper script to setup the Helix QAC project. It also includes some subcomponents:

* [findcpps](3rdpartytools/find_cpps/readme.md)
* [fix\_json](3rdpartytools/fix_json)
* [compare\_qaview](3rdpartytools/compare_qaview)


## <a name="use">How to use it</a>

The Helix configuration is working as follows:

* The basic tool installs to e.g. 

    > C:\Perforce\Helix-QAC-x.y.z

* The local Helix GUI can be called via 

    > C:\Perforce\Helix-QAC-x.y.z\common\bin\qagui.exe

* The plugins for MS Visual Studio / Eclipse can be installed from here

    > C:\Perforce\Helix-QAC-x.y.z\ide\_plugins

* The default configuration files are here

    > C:\Perforce\Helix-QAC-x.y.z\config\*

Helix creates a user specific configuration folder under AppData\Local

    > C:\Users\<YOUR\_NT\_USERNAME>\AppData\Local\Perforce\Helix-QAC-x.y.z

Clone the contents of this repo into that user specific configuration folder.    
You should then have the following files in these subdirectories:

Important here are the subfolders *config* and *user\_library*.

## The *config* folder holds the following configuration files:

* config/acf/prqa\<version\>\_\<release\>\_ccda\_cpp.acf
* config/acf/helix\<version\>\_\<release\>\_ccda\_cpp.acf

  > This is the _Analyser Config File (acf)_ and holdes the informations which checker modules with what version shall be used (e.g. qacpp v 4.3.0), which compiler config shall be used, and some coding-rule specific settings (e.g. metric thresholds).

* config/cct/ARM\_Compiler\_6\_A53.cct

  > This is the compiler config for ARM Compiler 6.6.1 with an ARMv8 Cortex-A53 target setting.

* config/cct/ARM\_Compiler\_6\_R7.cct

  > This is the compiler config for ARM Compiler 6.6.1 with an ARMv7 Cortex-R7 target setting.

* config/cct/ARM\_Compiler\_6\_R5.cct

  > This is the compiler config for ARM Compiler 6.6.1 with an ARMv7 Cortex-R5 target setting.

* config/cct/GHS\_201715\_standalone\_TC1V162\_C++11.cct

  > This is the compiler config for GHS Compiler 201715 with an Tricore/Aurix target setting.

* config/cct/GHS\_201815\_standalone\_TC1V162\_C++11.cct

  > This is the compiler config for GHS Compiler 201815 with an Tricore/Aurix target setting.

* config/cct/GHS\_201713\_testversion1i\_rh850\_C++11

  > This is the compiler config for GHS Compiler 201713 with an RH850 target setting.

* config/cct/GHS\_201815\_standalone\_RH850\_C++11

  > This is the compiler config for GHS Compiler 201815 with an RH850 target setting.

* config/rcf/prqa\<version\>\_\<release\>\_ccda\_cpp.rcf
* config/rcf/helix\<version\>\_\<release\>\_ccda\_cpp.rcf

  > This is the _Rule Config File (rcf)_ which holds the information, which codingrules (from MISRA, CERT, etc) shall be checked by the tool.

* config/ncf/prqa\_ccda\_config\_video\_cpp\_naming\_\<version\>.ncf

  > This is the _Name Config File (ncf)_ which holds the configuration to check for the C++ naming rules.


* config/qav/prqa\<version\>\_\<release\>\_ccda\_cpp.xml
* config/qav/helix\<version\>\_\<release\>\_ccda\_cpp.xml

  > This is the _Rule Config File for usage within QA-Verify projects_ which holds the information, which codingrules (from MISRA, CERT, etc) shall be checked by the tool and can be used via the "configgui.exe" tool to update the QA-Verify projects.

* config/vcf/prqa\_ccda\_config\_git\_\<version\>.xml

  > This is the _Version Control Config File (vcf)_ which holds the setup how to connect to the BIOS SocialCoding Bitbucket server via git.


### *user\_library* holdes additional codingrule-specific settings:

* user\_library\user\_messages\messages.xml

  > This file holds the mapping of the code metrics setup to the displayed warning messages. It is always valid for the latest release.

* user\_library\user\_messages\helix\<version\>\_\<release\>\_messages\_cpp.xml

  > This file holds the mapping of the code metrics setup to the displayed warning messages. It is always valid for the given release name in the filename.


* user\_library\user\_messages\helix\<version\>\_\<release\>\_messages\_cpp4helper.xml

  > This file holds the mapping of the code metrics setup to the displayed warning messages. It is always valid for the given release name in the filename. It is to be used with the "helix_helper" script for automated adaption of the help paths.


### Usage within Helix

To make use of these configuration files within the Helix GUI, please select the files described above in the Helix configuration GUI dropdown lists.


## <a name="contribute">How to contribute</a>

If you want to use this setup or contribute, please first contact the [Maintainers](#maintainers).

## <a name="feedback">Feedback</a>

Get in contact with the [Maintainers](#maintainers), e.g. via email or via the [coding rules T&R project](https://rb-tracker.bosch.com/tracker/projects/CDF/summary).
