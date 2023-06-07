#!/bin/bash

datetime=$(date +'%m_%d_%Y')
repo_dir=$1

total_interfaces=$(ls -A /sys/class/net | grep "enp" | wc -l)
if [[ $total_interfaces -lt 2 ]]
then
	echo "This is not a template machine. Will not update repo"
	exit 1
fi

update_repo() {
	trap 'fresh_clone' ERR

	rm -f **/*.lock
	git gc --prune=now
	git remote prune origin
	git fetch -p --recurse-submodules=no origin develop
	git checkout -f develop
	git reset --hard HEAD
	git clean -xffd
	git lfs fetch --recent
	git pull
	git submodule sync --recursive
	git submodule foreach --recursive "git reset --hard HEAD && git clean -xffd"
	git submodule foreach --recursive "git gc --prune=now && git remote prune origin"
	git submodule update --init --recursive --force
	git submodule foreach --recursive git lfs fetch --recent
}

fresh_clone() {
	echo "$HOSTNAME --- Do Fresh Clone"
	git_remote_url=`git remote get-url --push origin`
	git_remote_url=${git_remote_url:-ssh://git@sourcecode01.de.bosch.com:7999/vwag_e3/commonrepo.git}
	rm -rf $repo_dir/*
	rm -rf $repo_dir/.* 2>/dev/null
	set -e
	git clone $git_remote_url -b develop .
	git lfs fetch --recent
	git submodule sync --recursive
	git submodule foreach --recursive "git reset --hard HEAD && git clean -xffd"
	git submodule foreach --recursive "git gc --prune=now && git remote prune origin"
	git submodule update --init --recursive --force
	git submodule foreach --recursive "git lfs fetch --recent"
	end_run
}

end_run() {
	if [ $? -ne 0 ]; then
		echo "$HOSTNAME --- Update repo status on $datetime : FAILURE"
		exit 1
	else
		echo "$HOSTNAME --- Update repo status on $datetime : SUCCESS"
		exit 0
	fi
}

# MAIN EXECUTE
pushd $repo_dir
update_repo
popd
end_run
