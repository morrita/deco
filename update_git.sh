#!/bin/sh
# sends all updates to git

git add .
git status
git commit -am "update via update_git.sh"
git push origin master 
