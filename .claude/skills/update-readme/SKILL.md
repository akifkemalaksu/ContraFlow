---
name: update-readme
description: After every commit, checks if the README needs updating based on 
changed files and updates it automatically. Use this skill whenever the user 
commits code, asks to sync docs with code, or mentions README is out of date.
---

# Update README

After a commit, inspect the changed files and determine whether the README 
needs to reflect those changes. If so, update it and amend the commit.

## Steps

1. Read the current README.md
2. List the files changed in the last commit (`git diff HEAD~1 --name-only`)
3. Decide if any change affects what the README describes (new features, 
   removed commands, changed setup steps, etc.)
4. If an update is needed, edit README.md accordingly
5. Stage the change: `git add README.md`
6. Amend the commit preserving the original author:
   `git commit --amend --no-edit --reset-author`

## What to check for

- New or removed CLI commands / scripts
- Changed dependencies or install steps  
- Modified environment variables or config files
- Renamed or deleted files referenced in the README
- New features that should be documented