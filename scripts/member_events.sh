#!/bin/sh

./scripts/event_attendees.sh | grep --line-buffered $1 
