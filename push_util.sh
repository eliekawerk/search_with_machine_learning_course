if [[ $# -eq 0 ]] ; then
    echo 'please enter the commit message'
fi

echo "Pulling from remote branch"
git pull 

echo "Adding and committing all files"
git add . 

git commit -m "$1"

echo "Pushing changes"
git push


