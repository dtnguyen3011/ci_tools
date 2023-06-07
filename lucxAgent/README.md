# Clean WS directory on Lucx_agent machines

This script is used for clean up ws directory in lucxagent node

## Workflow diagram

$WORKSPACE\ws
    .lucx|lucx_agent@[0-9]*@tmp|lucx_agent@tmp|ci_tools => SKIP
    commonrepo
        Have "repo.git" => SKIP
        Have "repo" dir => REMOVE archive AND archive*@tmp
        Other           => REMOVE commonrepo AND commonrepo*@tmp
    lucx_agent
        Have "commonrepo|jenkins_pipelinescripts|logs|upstreamInfo" dir => SKIP
        Other       => REMOVE
        tmp file    => REMOVE over 3 days
    Other       => REMOVE over 7 days
    tmp file    => REMOVE over 3 days


## Author

XC-DA RADAR Continuous X (xcdaradarcontinuousx@bosch.com):
- Lam Trien Lap (MS/EDA15): Lap.LamTrien@vn.bosch.com
