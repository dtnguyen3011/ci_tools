$ws_path = "C:\JT\ws"
$dry_run_flag = $false
If (($args[0] -ne $null) -And ($args[0] -ne "")) {
    $ws_path = $args[0] + "\ws"
    If (($args[1] -ne $null) -And ($args[1] -ne "") -And ($args[1] -eq "dry-run")) {
        $dry_run_flag = $true
    }
}

$skip_dir_in_ws = ".lucx|lucx_agent@[0-9]*@tmp|lucx_agent@tmp|commonrepo@[0-9]*@tmp|ci_tools"
$skip_dir_in_lucx_agent = "commonrepo|jenkins_pipelinescripts|logs|upstreamInfo"

function Force_Remove_Dir {
    [CmdletBinding()]
    Param (
        [Parameter(Mandatory=$true,ValueFromPipeline=$true)]
        $Path
    )
    If (Test-Path -Path $Path) {
        If ($dry_run_flag) {
            Write-Output "  [WBRM] $Path"
        } Else {
            Remove-Item -path $Path -Recurse -Force
            Write-Output "  [DONE] $Path"
        }
    }
}

function Remove_Tmp_File_Older_Days {
    [CmdletBinding()]
    Param (
        [Parameter(Mandatory=$true,ValueFromPipeline=$true)] $Path,
        [Parameter(Mandatory=$true,ValueFromPipeline=$true)] $DaysToKeep
    )
    $TmpFile = "tmp_*.tmp"
    $DateTimeToKeep = $(Get-Date).AddDays(- $DaysToKeep)

    If ($dry_run_flag) {
        Write-Output "  [WBRM] $Path\$TmpFile over $DaysToKeep days"
    } Else {
        Get-Item $Path\$TmpFile | Where { $_.LastWriteTime -lt $DateTimeToKeep } | Remove-Item
        Write-Output "  [DONE] $Path\$TmpFile over $DaysToKeep days"
    }
}

function Clear_Ws_Commonrepo {
    [CmdletBinding()]
    Param (
        [Parameter(Mandatory=$true,ValueFromPipeline=$true)]
        $Commonrepo_Path
    )
    Write-Output "Go in $Commonrepo_Path"
    If (Test-Path -Path "$Commonrepo_Path\repo.git" -PathType Container) {
        Write-Output "  [SKIP] $Commonrepo_Path"
    } ElseIf (Test-Path -Path "$Commonrepo_Path\repo" -PathType Container) {
        Force_Remove_Dir "$Commonrepo_Path\archive"
        Force_Remove_Dir "$Commonrepo_Path\archive@tmp"
    } Else {
        Force_Remove_Dir "$Commonrepo_Path"
        Force_Remove_Dir "$Commonrepo_Path@tmp"
    }
    Remove_Tmp_File_Older_Days $Commonrepo_Path 3
}

function Clear_Ws_Lucxagent {
    [CmdletBinding()]
    Param (
        [Parameter(Mandatory=$true,ValueFromPipeline=$true)]
        $Lucxagent_Path
    )
    Write-Output "Go in $Lucxagent_Path"
    foreach ($lucx_sub_dir in (dir $Lucxagent_Path -Directory)) {
        If ($lucx_sub_dir -match $skip_dir_in_lucx_agent) {
            Write-Output "  [SKIP] $($lucx_sub_dir.FullName)"
        } Else {
            Force_Remove_Dir $($lucx_sub_dir.FullName)
        }
    }
    Remove_Tmp_File_Older_Days $Lucxagent_Path 3
}

function Clear_Ws_Other {
    [CmdletBinding()]
    Param (
        [Parameter(Mandatory=$true,ValueFromPipeline=$true)]
        $Other_Path
    )
    Write-Output "Go in $Other_Path"
    $DateTimeToKeep = $(Get-Date).AddDays(-7)
    $LastModifyTime = [datetime](Get-ItemProperty -Path $Other_Path -Name LastWriteTime).lastwritetime
    # Remove if over 7 days
    If ($LastModifyTime -lt $DateTimeToKeep) {
        Force_Remove_Dir $Other_Path
    } Else {
        Write-Output "  [SKIP] $Other_Path  -- (Not over 7 days)"
        Remove_Tmp_File_Older_Days $Other_Path 3
    }
}

function Main {
    foreach ($ws_sub_dir in (dir $ws_path -Directory)) {
        If ($ws_sub_dir -match $skip_dir_in_ws) {
            Write-Output "[SKIP] $($ws_sub_dir.FullName)"
        } ElseIf ($ws_sub_dir -match "commonrepo*") {
            Clear_Ws_Commonrepo $($ws_sub_dir.FullName)
        } ElseIf ($ws_sub_dir -match "lucx_agent*") {
            Clear_Ws_Lucxagent $($ws_sub_dir.FullName)
        } Else {
            Clear_Ws_Other $($ws_sub_dir.FullName)
        }
    }
    Remove_Tmp_File_Older_Days $ws_path 3
}

Main
