#!/bin/bash

wsPath="/var/jenkins/ws"
dryRunFlag=false
if [ ! -z "$1" ]; then
    wsPath="${1}/ws"
    if [ ! -z "$2" ] && [ "$2" == "dry-run" ]; then
        dryRunFlag=true
    fi
fi

SKIP_DIR_IN_WS="^(.lucx|lucx_agent@[0-9]*@tmp|lucx_agent@tmp|commonrepo@[0-9]*@tmp|ci_tools)$"
SKIP_DIR_IN_LUCX_AGENT="^(commonrepo|commonrepo@tmp|jenkins_pipelinescripts|jenkins_pipelinescripts@tmp|logs|upstreamInfo)$"

Force_Remove_Dir() {
    path=$1
    if [ -d "$path" ]; then
        if $dryRunFlag; then
            echo "  [WBRM] $path"
        else
            rm -rf $path
            echo "  [DONE] $path"
        fi
    fi
}

Remove_Tmp_File_Older_Days() {
    path=$1
    daysToKeep=$2

    tmpFile="tmp_*.tmp"
        if $dryRunFlag; then
        echo "  [WBRM] $path/$tmpFile over $daysToKeep days"
    else
        find $path -name "$tmpFile" -type f -mtime +$daysToKeep -delete
        echo "  [DONE] $path/$tmpFile over $daysToKeep days"
    fi
}

Clear_Ws_Commonrepo() {
    commonrepoPath=$1
    echo "Go in $commonrepoPath"
    if [ -d "$Commonrepo_Path/repo.git" ]; then
        echo "  [SKIP] $commonrepoPath"
    elif [ -d "$commonrepoPath/repo" ]; then
        Force_Remove_Dir "$commonrepoPath/archive"
        Force_Remove_Dir "$commonrepoPath/archive@tmp"
    else
        Force_Remove_Dir "$commonrepoPath"
        Force_Remove_Dir "$commonrepoPath@tmp"
    fi
    Remove_Tmp_File_Older_Days $commonrepoPath 3
}

Clear_Ws_Lucxagent() {
    lucxagentPath=$1
    echo "Go in $lucxagentPath"
    for lucxSubDir in $lucxagentPath/*; do
        if [ -d "$lucxSubDir" ]; then
            if [[ `basename "$lucxSubDir"` =~ $SKIP_DIR_IN_LUCX_AGENT ]]; then
                echo "  [SKIP] $lucxSubDir"
            else
                Force_Remove_Dir $lucxSubDir
            fi
        fi
    done

    Remove_Tmp_File_Older_Days $lucxagentPath 3
}

Clear_Ws_Other() {
    otherPath=$1
    dayToKeep=7
    echo "Go in $otherPath"
    dateFormat=`date --date="$dayToKeep days ago" +%Y-%m-%d`
    lastModifyTime=`stat $otherPath -c '%.10y'`
    # Remove if over 7 days
    if [[ $lastModifyTime < $dateFormat ]]; then
        Force_Remove_Dir $otherPath
    else
        echo "  [SKIP] $otherPath  -- (Not over $dayToKeep days)"
        Remove_Tmp_File_Older_Days $otherPath 3
    fi
}

Main() {
    for wsSubDir in $wsPath/*; do
        if [ -d "$wsSubDir" ]; then
            if [[ `basename "$wsSubDir"` =~ $SKIP_DIR_IN_WS ]]; then
                echo "[SKIP] $wsSubDir"
            elif [[ `basename "$wsSubDir"` =~ "commonrepo" ]]; then
                Clear_Ws_Commonrepo $wsSubDir
            elif [[ `basename "$wsSubDir"` =~ "lucx_agent" ]]; then
                Clear_Ws_Lucxagent $wsSubDir
            else
                Clear_Ws_Other $wsSubDir
            fi
        fi
    done
    Remove_Tmp_File_Older_Days $wsPath 3
}

Main
