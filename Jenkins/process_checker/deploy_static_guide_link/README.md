Static link to visible on developer side that guide them the way to control the PR

Deploy a local static link:
1. Copy "Process_Checker" folder to artifactory server.
Ex: https://rb-artifactory.bosch.com/ui/repos/tree/Properties/cc-da-radar-vwag-e3-release-local/VAG/Cx_Pipeline/Process_Checker
2. Use the link https://your_host_and_path/Process_Checker/Is_your_PR_ready_to_merge.html?pr=PR_number to put into Bitbucket build status
Ex: https://rb-artifactory.bosch.com/artifactory/cc-da-radar-vwag-e3-release-local/VAG/Cx_Pipeline/Process_Checker/Is_your_PR_ready_to_merge.html?pr=12345