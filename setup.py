"""
Talon-Fmt
"""

from setuptools import setup

import os


with open(os.path.join(os.path.dirname(__file__), "README.md")) as f:
    LONG_DESCRIPTION = f.read()


setup(
    name="talonfmt",
    version="0.0.1",
    maintainer="Wen Kokke",
    maintainer_email="me@wen.works",
    author="Wen Kokke",
    author_email="me@wen.works",
    url="https://github.com/wenkokke/talonfmt",
    license="MIT",
    platforms=["any"],
    python_requires=">=3.3",
    description="Formatter for Talon files",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Topic :: Software Development :: Compilers",
        "Topic :: Text Processing :: Linguistic",
    ],
    packages=["talonfmt"],
    project_urls={"Source": "https://github.com/wenkokke/talonfmt"},
    install_requires=[
        "overrides",
        "more_itertools",
        "tree_sitter_talon @ git+https://github.com/wenkokke/py-tree-sitter-talon.git@v1.2.1#egg=tree_sitter_talon",
        "pytest",
        "pytest-golden",
    ],
)
