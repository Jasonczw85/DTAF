import optparse
import zipfile
import sys
import os

def Unzipfile(zip_pac_path, dest):
	zip_packages = zip_pac_path.split(';')
	for zip_pac in zip_packages:
		if os.path.exists(zip_pac):
			zipfiles = zipfile.ZipFile(zip_pac, 'r')
			zipfiles.extractall(dest)
			zipfiles.close()
			print "Unzip finished!"

def main():
	parser = optparse.OptionParser()

	parser.add_option("-s", "--source-zip",
                      dest = "zip_source",
                      metavar = 'ZIP_SOURCE',
                      action = "store",
                      default = "",
                      help = "Specify zip source full path"
                      "\n(default = "")"
		             )

	parser.add_option("-d", "--unzip-dest",
		              dest = "unzip_dest",
		              metavar = "UNZIP_DEST",
		              action = "store",
		              default = "",
		              help = "Specify path unzipped to"
		              "\n(default = "")"
		              )

	options, args = parser.parse_args()

	Unzipfile(options.zip_source, options.unzip_dest)

if __name__ == '__main__':
	sys.exit(main())