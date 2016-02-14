import os
from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-protractor-new',
    version='0.9.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=['django>=1.4'],
    license='MIT License',  # example license
    description='Easily integrate your protractor tests with django',
    long_description=README,
    author='Jared Hellman (formerly James Pulec)',
    author_email='jhellma1@gmail.com',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
    ],
)
