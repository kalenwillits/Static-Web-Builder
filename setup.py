"""Setup script for swb package."""

from setuptools import setup, find_packages
from swb import __version__

setup(
    name='swb',
    version=__version__,
    description='Static Web Builder - build and deploy static websites',
    author='swb contributors',
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'swb': [
            'templates/*',
            'resources/*',
        ],
    },
    install_requires=[
        'markdown>=3.1',
        'Jinja2>=3.0',
        'PyYAML>=6.0',
        'Pygments>=2.0',
    ],
    entry_points={
        'console_scripts': [
            'swb=swb.cli:main',
        ],
    },
    python_requires='>=3.12',
)
