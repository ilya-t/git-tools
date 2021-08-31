#!/bin/bash
#Cherry-picks only last commit from branch:
#   git.code_review_branch.sh branch_name
#Cherry-picks only 3 last commits from branch:
#   git.code_review_branch.sh branch_name 3
ORIGIN_BRANCH="$(git branch | grep \* | sed 's/\* //')"
CODE_REVIEW_BRANCH=cdrw/$1
BRANCH_TO_REVIEW=$1
COMMITS_TO_PICK=$2

if [ "$COMMITS_TO_PICK" == "" ]; then
    COMMITS_TO_PICK=1
fi

let COUNTDOWN=COMMITS_TO_PICK-1
COMMITS_LIST=""
while [ $COUNTDOWN -ge 0 ]; do
    COMMITS_LIST=$COMMITS_LIST"origin/$BRANCH_TO_REVIEW~$COUNTDOWN "
    let COUNTDOWN=COUNTDOWN-1
done

echo "CODE REVIEW: $BRANCH_TO_REVIEW"
git branch -D $CODE_REVIEW_BRANCH

set -e
echo "FETCHING BRANCH:"
eval "git fetch origin "$BRANCH_TO_REVIEW


echo "Before we proceed to review take a look at 'git status':"
git status --short #--untracked-files=no

echo ""
read -p "Is it okay to proceed? (y/n(q)) " CONFIRM

if [ "$CONFIRM" == "q" ] || [ "$CONFIRM" == "n" ] || [ "$CONFIRM" == "N" ] ; then
    exit 0;
fi

git checkout -b $CODE_REVIEW_BRANCH

set +e
echo "CHERRY PICKING:"
eval "git cherry-pick "$COMMITS_LIST
if [ "$?" != "0" ] ; then
    git cherry-pick --abort
    eval "git checkout $ORIGIN_BRANCH"
    eval "git branch -D "$CODE_REVIEW_BRANCH
    echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
    echo "Failed to cherry-pick! You've returned where you were!"
    echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
    exit 0;
fi
set +e
# "origin/"$BRANCH_TO_REVIEW"~0"

#git branch --move $CODE_REVIEW_BRANCH
# TODO: ask for soft reset at the end and enter codereview mode
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
echo CodeReview of $BRANCH_TO_REVIEW
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"

read -p "How about 'git reset --soft HEAD~$COMMITS_TO_PICK'? (y/n(q)) " CONFIRM_RESET
if [ "$CONFIRM_RESET" != "q" ] && [ "$CONFIRM_RESET" != "n" ] && [ "$CONFIRM_RESET" != "N" ] ; then
    eval "git reset --soft HEAD~$COMMITS_TO_PICK"
    echo "DONE! Take a look:"
    git status --short --untracked-files=no

    read -p "If you're done, how about 'git reset --hard'? (y/n(q)) " CONFIRM_DONE
    if [ "$CONFIRM_DONE" != "q" ] && [ "$CONFIRM_DONE" != "n" ] && [ "$CONFIRM_DONE" != "N" ] ; then
        git reset --hard
    fi
else
    echo "DONE! Take a look:"
    eval "git log --pretty=oneline --abbrev-commit -$COMMITS_TO_PICK"
fi

read -p "Is review finished? (y/n(q)) " CONFIRM_FINISH

if [ "$CONFIRM_FINISH" != "q" ] && [ "$CONFIRM_FINISH" != "n" ] && [ "$CONFIRM_FINISH" != "N" ] ; then
    eval "git checkout $ORIGIN_BRANCH"
    eval "git branch -D "$CODE_REVIEW_BRANCH

    echo "Done! You've returned where you were!"
    exit 0;
fi
