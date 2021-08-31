#!/usr/bin/env sh
set -e

git init
git config --local user.email "user@email.com"
git config --local user.name "UserName"
# master commits
echo "#temporary repository!" > README.md
git add README.md
git commit --message 'Initial Commit'
echo "# Intergration tests temporary repository!" > README.md
git commit --all --message 'upd README'

# dev commits
git checkout -b dev
echo "dev initial state" > dev_file
git add * && git commit --message 'add "dev_file"'

# feature#1 commits
git checkout -b feature_1
echo "f1 initial state" > f1_to_be_deleted
git add * && git commit --message 'add "f1_to_be_deleted"'
rm f1_to_be_deleted
git commit --all --message 'remove "f1_to_be_deleted"'
echo "f1 initial state" > f1_file
git add * && git commit --message 'add "f1_file"'

# feature#2 commits
git checkout -b feature_2
echo "f2 initial state" > f2_file
git add * && git commit --message 'add "f2_file"'

# hotfix commits
git checkout -b hotfix master
echo "hotfix initial state" > hotfix_file
git add * && git commit --message 'add "hotfix_file"'
