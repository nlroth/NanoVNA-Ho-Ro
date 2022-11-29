#!/bin/sh

VERSION=$(grep -E '#define[[:space:]]+VERSION[[:space:]]+\"[0-9]*\.[0-9]*\.[0-9]*' main.c | cut -d\" -f2)
PROJECT=NanoVNA-H-noSD_$VERSION
BUILD=build

# show size info
# arm-none-eabi-size $BUILD/$PROJECT.elf

# 128K for -H
FLASH_SIZE=$((0x20000))

PAGE_SIZE=$((0x800))
# one CONFIG slot
SAVE_CONFIG_SIZE=$PAGE_SIZE
# up to 8 PROP_CONFIG slots
SAVE_PROP_CONFIG_SIZE=$((3 * $PAGE_SIZE))

# get segment sizes
TEXT_DATA_BSS=$(arm-none-eabi-size $BUILD/$PROJECT.elf | tail -1)
TEXT=$(echo $TEXT_DATA_BSS | cut -d\  -f1)
DATA=$(echo $TEXT_DATA_BSS | cut -d\  -f2)
BSS=$(echo $TEXT_DATA_BSS | cut -d\  -f3)
#echo $TEXT $DATA $BSS

# used program and data flash space
USED_FLASH=$(( $TEXT + $DATA ))
# free flash space available for persistent storage
FREE_FLASH=$(( FLASH_SIZE - $USED_FLASH ))
# flash space for slots
PROP_CONFIG_SPACE=$(( $FREE_FLASH - $SAVE_CONFIG_SIZE ))
# number of slots
SAVEAREA_MAX=$(( $PROP_CONFIG_SPACE / $SAVE_PROP_CONFIG_SIZE ))
# calculate the space between prog+data and config (safety margin)
UNUSED=$(( $FREE_FLASH - $SAVE_CONFIG_SIZE - SAVE_PROP_CONFIG_SIZE * $SAVEAREA_MAX ))

# show the results
echo "Used flash:  $USED_FLASH bytes ($(( ($USED_FLASH + $PAGE_SIZE -1) / $PAGE_SIZE )) 2K-pages)"
echo "Free flash:  $FREE_FLASH bytes ($(( $FREE_FLASH / $PAGE_SIZE )) 2K-pages)"
echo "Config space: $PAGE_SIZE bytes ( 1 2K-page)"
echo "SAVEAREA_MAX: $SAVEAREA_MAX slots    ($(( $SAVEAREA_MAX * 3 )) 2K-pages)"
echo "Unused flash: $UNUSED bytes"

