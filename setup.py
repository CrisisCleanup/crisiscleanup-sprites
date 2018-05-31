import os

from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))

packages = ['sprites']

requires = [
    'Pillow>=5.1.0'
]

with open('README.md', 'r') as f:
    readme = f.read()

setup(
    name="crisiscleanup-sprites",
    version="0.1.0",
    description="A tool and resources for producing sprites for the CrisisCleanup map",
    long_description=readme,
    long_description_content_type='text/markdown',
    author="Crisis Cleanup",
    packages=packages,
    package_data={'': ['../README.md']},
    package_dir={'sprites': 'sprites'},
    include_package_data=True,
    python_requires=">=3.5",
    install_requires=requires,
    zip_safe=True,
    classifiers=(
        'Natural Language :: English',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy'
    )
)