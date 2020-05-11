#!/bin/sh
UPSTREAM="origin/master"
LOCAL=$(git rev-parse @)
REMOTE=$(git rev-parse "$UPSTREAM")
BASE=$(git merge-base @ "$UPSTREAM")

if [ $LOCAL = $REMOTE ]
then
	echo "No new update."
	exit 0
fi
echo "Start updating new version..."
git pull

#TODO database migrate

#TODO force reload with upstart