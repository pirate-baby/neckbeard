#!/bin/bash
set -e
# for every line in the repos.txt run this command
for repo in $(cat repos.txt); do
    docker run --env-file .env -v ${PWD}:/app --rm neckbeard  $repo
done