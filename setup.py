from setuptools import setup, find_namespace_packages
from os import path
from common_dependencies import common_dependencies, develop, install

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

PACKAGE_NAME = 'snet.sdk'


version_dict = {}
with open("./snet/sdk/version.py") as fp:
    exec(fp.read(), version_dict)

setup(
    name=PACKAGE_NAME,
    version=version_dict['__version__'],
    packages=find_namespace_packages(include=['snet.*']),
    namespace_packages=['snet'],

    url='https://github.com/singnet/snet-sdk-python',
    license='MIT',
    author='SingularityNET Foundation',
    author_email='info@singularitynet.io',
    description='SingularityNET Python SDK',
    python_requires='>=3.11',
    install_requires=common_dependencies,
    long_description=long_description,
    long_description_content_type='text/markdown'
)
