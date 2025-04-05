from setuptools import setup, find_packages

setup(
    name="stock_screener",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "requests",
        "pandas",
        "openai",
        "finvizfinance",
    ],
    entry_points={
        "console_scripts": [
            "stock-screener=stock_screener.main:main",
        ],
    },
) 