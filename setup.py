#!/usr/bin/env python3
"""
GTach Application Setup Configuration

Created: 2025 08 06
"""

from setuptools import setup, find_packages

setup(
    name="gtach",
    version="1.0.0",
    description="GTach Embedded Application System",
    author="William Watson",
    author_email="william.watson@example.com",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.9",
    install_requires=[
        # Core dependencies will be added as needed
    ],
    extras_require={
        "pi": [
            "RPi.GPIO>=0.7.0",
        ],
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "gtach=main:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS :: MacOS X",
    ],
)
