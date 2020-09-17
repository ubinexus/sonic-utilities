.ONESHELL:
SHELL = /bin/bash
.SHELLFLAGS += -e

MAIN_TARGET = sonic-utilities-data_1.0-1_all.deb

$(MAIN_TARGET):
	pushd ./src

	# Build the package
	dpkg-buildpackage -rfakeroot -b -us -uc

	popd

clean:
	pushd ./src
	dpkg-buildpackage -rfakeroot -Tclean
	popd
	rm -rf $(MAIN_TARGET) *.buildinfo *.changes
