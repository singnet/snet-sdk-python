import os
from setuptools import find_namespace_packages, setup

from version import __version__

PACKAGE_NAME = 'snet.sdk'


this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


with open("./requirements.txt") as f:
    requirements_str = f.read()
requirements = requirements_str.split("\n")


setup(
    name=PACKAGE_NAME,
    version=__version__,
    packages=find_namespace_packages(include=['snet.*']),
    namespace_packages=['snet'],
    url='https://github.com/singnet/snet-sdk-python',
    author='SingularityNET Foundation',
    author_email='info@singularitynet.io',
    description='SingularityNET Python SDK',
    long_description=long_description,
    long_description_content_type='text/markdown',
    license='MIT',
    python_requires='>=3.10',
    install_requires=requirements,
    include_package_data=True
)
