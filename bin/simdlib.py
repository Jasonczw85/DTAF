import re
import os
import shutil

simdlib_old = open("Dolby_Intrinsics_Imp/Source_Code/dlb_intrinsics/dlb_intrinsics.h")
simdlib_new = open("dlb_intrinsics.h", "w")
for line in simdlib_old.readlines():
	if re.match("#include \"dlb_simdlib\/dlb_simdlib.h\"", line):
		line = ""
	simdlib_new.write(line)

simdlib_old.close()
simdlib_new.close()

os.remove("Dolby_Intrinsics_Imp/Source_Code/dlb_intrinsics/dlb_intrinsics.h")
shutil.copy("dlb_intrinsics.h", "Dolby_Intrinsics_Imp/Source_Code/dlb_intrinsics/")
