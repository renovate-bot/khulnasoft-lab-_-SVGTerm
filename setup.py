#!/usr/bin/env python3

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="svgterm",
    version="2.0.0",  # Major version bump for Python 3.7+ support
    license="BSD 3-clause license",
    author="KhulnaSoft Lab",
    author_email="info@khulnasoft.com",
    description="Record terminal sessions as SVG animations",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/khulnasoft-lab/svgterm",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: MacOS",
        "Operating System :: POSIX :: BSD",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: System :: Shells",
        "Topic :: Terminals",
        "Topic :: Multimedia :: Graphics :: Presentation",
        "Topic :: Multimedia :: Graphics :: Graphics Conversion",
    ],
    python_requires=">=3.7",
    packages=find_packages(exclude=["tests*"]),
    scripts=["scripts/svgterm"],
    include_package_data=True,
    install_requires=[
        "lxml>=4.6.0,<6.0.0",
        "pyte>=0.8.0,<1.0.0",
        "wcwidth>=0.2.0,<0.3.0",
        "typing-extensions>=4.0.0,<5.0.0;python_version<'3.8'",
    ],
    extras_require={
        "dev": [
            "black>=23.0.0",
            "coverage>=7.0.0",
            "mypy>=1.0.0",
            "pylint>=3.0.0",
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "twine>=4.0.0",
            "wheel>=0.40.0",
        ],
        "test": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/khulnasoft-lab/svgterm/issues",
        "Source": "https://github.com/khulnasoft-lab/svgterm",
    },
)
