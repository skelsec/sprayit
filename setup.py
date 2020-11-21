from setuptools import setup, find_packages
import re

VERSIONFILE="sprayit/_version.py"
verstrline = open(VERSIONFILE, "rt").read()
VSRE = r"^__version__ = ['\"]([^'\"]*)['\"]"
mo = re.search(VSRE, verstrline, re.M)
if mo:
    verstr = mo.group(1)
else:
    raise RuntimeError("Unable to find version string in %s." % (VERSIONFILE,))


setup(
	# Application name:
	name="sprayit",

	# Version number (initial):
	version=verstr,

	# Application author details:
	author="Tamas Jos",
	author_email="info@skelsecprojects.com",

	# Packages
	packages=find_packages(),

	# Include additional files into the package
	include_package_data=True,


	# Details
	url="https://github.com/skelsec/sprayit",

	zip_safe = False,
	#
	# license="LICENSE.txt",
	description="Password spraying",
	long_description="Password spraying",

	# long_description=open("README.txt").read(),
	python_requires='>=3.7',
	classifiers=(
		"Programming Language :: Python :: 3.7",
		"Programming Language :: Python :: 3.8",
		"License :: OSI Approved :: MIT License",
		"Operating System :: OS Independent",
	),
	install_requires=[
		'msldap>=0.3.21',
		'asysocks>=0.0.10',
		'tqdm',
	],
	entry_points={
		'console_scripts': [
			'sprayit = sprayit.__main__:main',
		],
	}
)