#!/usr/bin/env bash
TREETOWALK = '/home/jsanford/gitDev/lib.unb.ca-webtree/core'

cd $TREETOWALK
find . -type f -print0 | xargs -0 sed -i 's/\@ *include/include/g'
find . -type f -print0 | xargs -0 sed -i 's/\@ *require/require/g'
