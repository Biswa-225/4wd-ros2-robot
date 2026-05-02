from setuptools import find_packages, setup

# Packaging file for installing Rosmaster_Lib into Python.
# The ROS driver imports `from Rosmaster_Lib import Rosmaster`, so this package
# must be installed or available on PYTHONPATH on the Raspberry Pi.
setup(
    name='Rosmaster_Lib',
    version='3.3.9',
    author='Yahboom Team',
    packages=find_packages(),
)

# Manual install command kept for reference:
# cd py_install
# sudo python3 setup.py install
