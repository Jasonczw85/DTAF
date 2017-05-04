#!/bin/bash

# This script will create the Beagleboard backends in the ddp_udc 
# folder based on the tisim backends. It will copy the original Makefile from
# the tisim folder into the beagleboard one and apply the required changes

BASE_DIR="$( cd -P "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo $BASE_DIR
MAKE_DIRS="${BASE_DIR}/make/ddp_udc/"

TI_REGEX="tisim_*_c64*"
CURR_COMPILER="cl6x"
CURR_LINKER="lnk6x"
NEW_COMPILER="c6runapp-cc"
NEW_LINKER="c6runapp-cc"

# print usage information
usage()
{
  echo -e "# Generates the C64x Beagleboard Makefiles out of the tisim Makefiles"
  echo -e "# located in [MAKE_DIR]."
  echo -e "# The script will recursively search all '${TI_REGEX}' subfolders"
  echo -e "# of [MAKE_DIR] and create a '${TI_REGEX//tisim/beagleboard}' at the same level "
  echo -e "# containing an equivalent c64x beagleboard Makefile"
  echo -e "# "
  echo -e "# Usage: $0 [optional MAKE_DIR]"
  echo -e "#  optional MAKE_DIR        The path containing the tisim folders"
  echo -e "#  If no MAKE_DIR argument is specified, the following default location"
  echo -e "#  will be used:"
  echo -e "#  ${MAKE_DIRS}"
  echo -e "# "
  echo -e "#  -h                       Print this message and exit."
  exit 0
}

if [[ $# -gt 0 ]]; then
  if [[ $1 == "-h" ]]; then 
	usage
  elif [[ ! -d $1 ]]; then
	echo -e "# Given MAKE_DIR does not exist."; exit 2;
  else
	MAKE_DIRS=$1
  fi
fi


echo -e "\n# Searching for ${TI_REGEX}/Makefile in ${MAKE_DIRS}"
for TIBACK in `find ${MAKE_DIRS} -type d -name "${TI_REGEX}"` ; do
        echo $TIBACK
#	BEAGLE_DIR=${TIBACK//tisim/beagleboard}
	BEAGLE_DIR=`echo $TIBACK | sed "s:tisim:beagleboard:"`
#	BEAGLE_DIR=${BEAGLE_DIR//ccs/c6run}
	BEAGLE_DIR=`echo $BEAGLE_DIR | sed "s:ccs:c6run:"`

	TI_MAKEFILE="${TIBACK}/Makefile"
	BB_MAKEFILE="${BEAGLE_DIR}/Makefile"

	# Check if Makefile exists
	if [[ ! -e ${TI_MAKEFILE} ]]; then continue; fi

	# create beagleboard backends dir
	mkdir -p ${BEAGLE_DIR}

	echo -e "\n# $(basename $TIBACK) -> $(basename $BEAGLE_DIR)"

	# copy original Makefile to beagleboard backend and apply changes
	echo -e -n "   -> copying ${TI_MAKEFILE} -> ${BB_MAKEFILE}... "
	cp -f ${TI_MAKEFILE} ${BB_MAKEFILE}
	echo -e "done."

	# replace compiler
	echo -e -n "   -> replacing compiler... "
	sed -i "s|${CURR_COMPILER}|${NEW_COMPILER}|g" ${BB_MAKEFILE}
	echo -e "done."

	# replace linker
	echo -e -n "   -> replacing linker... "
	sed -i "s|${CURR_LINKER}|${NEW_LINKER}|g" ${BB_MAKEFILE}
	echo -e "done."

	# replace CFLAGS not recognized by c6runapp-cc
	echo -e -n "   -> replacing CFLAGS --output_file... "
	sed -i 's/--output_file=$@/-o $@/g' ${BB_MAKEFILE}
	echo -e "done."

	# replace CFLAGS not recognized by c6runapp-cc
	echo -e -n "   -> replacing CFLAGS... "
	sed -i 's/$(CFLAGS_OUTPUT_DIR_ddp_udc.*/-o $@ $</' ${BB_MAKEFILE}
	echo -e "done."

	# replace @$(CCDEP_ not recognized by c6runapp-cc
	echo -e -n "   -> replacing CCDEP_... "
	sed -i 's/@$(CCDEP_/# @$(CCDEP_/g' ${BB_MAKEFILE}
	echo -e "done."
    
	# replace ddp_udc_tisim to avoid confusion
	echo -e -n "   -> replacing .ddp_udc_tisim... "
	sed -i 's/.ddp_udc_tisim/.ddp_udc_beagleboard/g' ${BB_MAKEFILE}
	echo -e "done."

	# remove unnecessary rts library include
	echo -e -n "   -> removing rts64plus.lib... "
	sed -i 's/-lrts64plus.lib/ /' ${BB_MAKEFILE}
	sed -i 's/-lrts6400.lib/ /' ${BB_MAKEFILE}
	echo -e "done."

	# replacing binary names
	echo -e -n "   -> replacing binaries names... "
	sed -i "s|ddp_udc_c64_release.out|ddp_udc_c64_c6run_release.axf|g" ${BB_MAKEFILE}
	sed -i "s|ddp_udc_c64_debug.out|ddp_udc_c64_c6run_debug.axf|g" ${BB_MAKEFILE}
	sed -i "s|ddp_udc_c64plus_release.out|ddp_udc_c64plus_c6run_release.axf|g" ${BB_MAKEFILE}
	sed -i "s|ddp_udc_c64plus_debug.out|ddp_udc_c64plus_c6run_debug.axf|g" ${BB_MAKEFILE}
	
	echo -e "done."
	

done
echo -e "finished."
