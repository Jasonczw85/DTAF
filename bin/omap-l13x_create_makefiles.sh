# This script will create the Beagleboard backends in the ddp_udc 
# folder based on the tisim backends. It will copy the original Makefile from
# the tisim folder into the omap-l13x one and apply the required changes

BASE_DIR="$( cd -P "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo $BASE_DIR
MAKE_DIRS="${BASE_DIR}"

#TI_REGEX="tisim_*_c64*"
TI_REGEX_LIST=(tisim_*_c64* tisim_*_c674* tisim_*_c67*)
CURR_COMPILER="cl6x"
CURR_LINKER="lnk6x"
NEW_COMPILER="c6runapp-cc"
NEW_LINKER="c6runapp-cc"

# print usage information
usage()
{
  echo -e "# Generates the OMAP-L13x board Makefiles out of the tisim Makefiles"
  echo -e "# located in [MAKE_DIR]."
  echo -e "# The script will recursively search all '${TI_REGEX}' subfolders"
  echo -e "# of [MAKE_DIR] and create a '${TI_REGEX//tisim/omap-l13x}' at the same level "
  echo -e "# containing an equivalent c64x omap-l13x Makefile"
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

convert_makefiles()
{
	echo -e "\n# Searching for $1/Makefile in ${MAKE_DIRS}"
	for TIBACK in `find ${MAKE_DIRS} -type d -name "$1"` ; do

		OMAP_L13x_DIR=${TIBACK//tisim/omap-l13x}
		OMAP_L13x_DIR=${OMAP_L13x_DIR//ccs/c6run}

		TI_MAKEFILE="${TIBACK}/Makefile"
		OL_MAKEFILE="${OMAP_L13x_DIR}/Makefile"

		# Check if Makefile exists
		if [[ ! -e ${TI_MAKEFILE} ]]; then continue; fi

		# create omap-l13x backends dir
		mkdir -p ${OMAP_L13x_DIR}

		echo -e "\n# $(basename $TIBACK) -> $(basename $OMAP_L13x_DIR)"

		# copy original Makefile to omap-l13x backend and apply changes
		echo -e -n "   -> copying ${TI_MAKEFILE} -> ${OL_MAKEFILE}... "
		cp -f ${TI_MAKEFILE} ${OL_MAKEFILE}
		echo -e "done."

		# replace compiler
		echo -e -n "   -> replacing compiler... "
		sed -i "s|\(^CC_.*\)${CURR_COMPILER}|\1${NEW_COMPILER}|g" ${OL_MAKEFILE}
		echo -e "done."

		# replace linker
		echo -e -n "   -> replacing linker... "
		sed -i "s|${CURR_LINKER}|${NEW_LINKER}|g" ${OL_MAKEFILE}
		echo -e "done."

		# replace CFLAGS not recognized by c6runapp-cc
		#echo -e -n "   -> replacing CFLAGS... "
		#sed -i 's/$(CFLAGS_OUTPUT_DIR_ddp_udc.*/-o $@ $</' ${OL_MAKEFILE}
		#echo -e "done."

		# replace CCDEP_FLAGS not recognized by c6runapp-cc
		echo -e -n "   -> replacing CCDEP_FLAGS... "
		sed -i 's/--preproc_dependency/-ppd/' ${OL_MAKEFILE}
		echo -e "done."
		
		# replace CCDEP_FLAGS not recognized by c6runapp-cc
		echo -e -n "   -> replacing CCDEP_FLAGS... "
		sed -i 's/--output_file=$@/-o\ $@/' ${OL_MAKEFILE}
		echo -e "done."
		
		# remove unnecessary rts library include
		echo -e -n "   -> removing rts64plus.lib... "
		sed -i 's/-lrts[A-Za-z0-9]*.lib\>/ /' ${OL_MAKEFILE}
        #sed -i 's/-lrts6400.lib/ /' ${OL_MAKEFILE}
		echo -e "done."

		# replacing binary names
		echo -e -n "   -> replacing binaries names... "
		sed -i "s|\.out|\.axf|g" ${OL_MAKEFILE}
		#sed -i "s|ddp_udc_c64_release.out|ddp_udc_c64_c6run_release.axf|g" ${OL_MAKEFILE}
		#sed -i "s|ddp_udc_c64_debug.out|ddp_udc_c64_c6run_debug.axf|g" ${OL_MAKEFILE}
		#sed -i "s|ddp_udc_c64plus_release.out|ddp_udc_c64plus_c6run_release.axf|g" ${OL_MAKEFILE}
		#sed -i "s|ddp_udc_c64plus_debug.out|ddp_udc_c64plus_c6run_debug.axf|g" ${OL_MAKEFILE}
		
		echo -e "done."
	done
}


# Main
if [[ $# -gt 0 ]]; then
  if [[ $1 == "-h" ]]; then 
	usage
  elif [[ ! -d $1 ]]; then
	echo -e "# Given MAKE_DIR does not exist."; exit 2;
  else
	MAKE_DIRS=$1
  fi
fi

for TI_REGEX in ${TI_REGEX_LIST[*]}; do
	convert_makefiles $TI_REGEX
done

echo -e "finished."
