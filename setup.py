#!/usr/bin/env python
"""Setup script for hanzo-aci package."""

import os
from setuptools import setup, find_packages

# Load version from version.py
version = {}
with open(os.path.join("hanzo_aci", "version.py")) as f:
    exec(f.read(), version)

# Load long description from README.md
with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="hanzo-aci",
    version=version["__version__"],
    description="Abstract Computer Interface for AI assistants",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Hanzo AI",
    author_email="dev@hanzo.ai",
    url="https://github.com/hanzo-ai/aci",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
    python_requires=">=3.10",
    install_requires=[
        "asyncio",
    ],
    extras_require={
        "mcp": ["hanzo-mcp>=0.1.29"],
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.20.0",
            "black>=23.3.0",
            "ruff>=0.1.0",
            "pytest-cov>=4.1.0",
        ],
        "all": [
            "hanzo-mcp>=0.1.29",
        ],
    },
    entry_points={
        "console_scripts": [
            "hanzo-aci=hanzo_aci.cli:main",
        ],
    },
)
