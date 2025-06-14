#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
小红书搜索工具 (XiaoHongShu Search)
一个功能强大的小红书笔记搜索和访问工具，支持智能排序、双重访问方式和自动认证。
"""

from setuptools import setup, find_packages
import os

# 读取README文件
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# 读取requirements.txt
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="xiaohongshu-search",
    version="1.0.0",
    author="Derek Zhou",
    author_email="derekzhou1979@gmail.com",
    description="一个功能强大的小红书笔记搜索和访问工具，支持智能排序、双重访问方式和自动认证",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/DerekZhou1979/xiaohongshu-search",
    project_urls={
        "Bug Reports": "https://github.com/DerekZhou1979/xiaohongshu-search/issues",
        "Source": "https://github.com/DerekZhou1979/xiaohongshu-search",
        "Documentation": "https://github.com/DerekZhou1979/xiaohongshu-search#readme",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Indexing",
        "Framework :: Flask",
        "Environment :: Web Environment",
        "Natural Language :: Chinese (Simplified)",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
        ],
        "test": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.10.0",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.txt", "*.md", "*.yml", "*.yaml", "*.json"],
        "static": ["*"],
        "templates": ["*.html"],
    },
    entry_points={
        "console_scripts": [
            "xiaohongshu-search=app:main",
        ],
    },
    keywords=[
        "xiaohongshu",
        "小红书",
        "search",
        "搜索",
        "web-scraping",
        "flask",
        "selenium",
        "crawler",
        "爬虫",
        "social-media",
        "content-analysis",
    ],
    zip_safe=False,
) 