import os
from setuptools import find_namespace_packages, setup
# from setuptools.command.develop import develop as _develop
# from setuptools.command.install import install as _install

from version import __version__

PACKAGE_NAME = 'snet.sdk'


this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


with open("./requirements.txt") as f:
    requirements_str = f.read()
requirements = requirements_str.split("\n")


# def install_and_compile_proto():
#     from snet.sdk.utils.utils import compile_proto
#     from pathlib import Path
#     proto_dir = Path(__file__).absolute().parent.joinpath(
#         "snet", "sdk", "resources", "proto")
#     dest_dir = Path(snet.sdk.__file__).absolute(
#     ).parent.joinpath("resources", "proto")
#     print(proto_dir, "->", dest_dir)
#     for fn in proto_dir.glob('*.proto'):
#         print("Compiling protobuf", fn)
#         compile_proto(proto_dir, dest_dir, proto_file=fn)


# class develop(_develop):
#     """Post-installation for development mode."""

#     def run(self):
#         _develop.run(self)
#         self.execute(install_and_compile_proto, (),
#                      msg="Compile protocol buffers")


# class install(_install):
#     """Post-installation for installation mode."""

#     def run(self):
#         _install.run(self)
#         self.execute(install_and_compile_proto, (),
#                      msg="Compile protocol buffers")


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
    # cmdclass={
    #     'develop': develop,
    #     'install': install
    # },
    include_package_data=True
)
