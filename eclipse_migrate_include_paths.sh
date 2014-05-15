#!/usr/bin/env bash
TREETOWALK="/home/jsanford/gitDev/lib.unb.ca-webtree"

cd $TREETOWALK
find . -type f -print0 | xargs -0 sed -i 's/\"\/www\//\"\/var\/www\/lib.unb.ca\/htdocs\//g'
find . -type f -print0 | xargs -0 sed -i "s/'\/www\//'\/var\/www\/lib.unb.ca\/htdocs\//g"
