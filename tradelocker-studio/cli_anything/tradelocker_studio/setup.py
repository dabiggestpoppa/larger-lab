from setuptools import setup, find_namespace_packages

setup(
    name="cli-anything-tradelocker-studio",
    version="0.1.0",
    description="CLI harness for TradeLocker Studio — write bot code, run backtests, read results",
    packages=find_namespace_packages(include=["cli_anything.*"]),
    python_requires=">=3.11",
    install_requires=[
        "click>=8.0",
        "requests>=2.28",
    ],
    entry_points={
        "console_scripts": [
            "tl-studio=cli_anything.tradelocker_studio.cli_studio:cli",
        ],
    },
)
