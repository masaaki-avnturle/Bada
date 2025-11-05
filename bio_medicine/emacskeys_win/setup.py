from setuptools import setup, find_packages

setup(
    name="emacskeys_win",
    version="0.1.0",
    description="Per-app Emacs-like keybindings for Windows (ctypes, no pywin32 required)",
    packages=find_packages(where="lib"),
    package_dir={"": "lib"},
    entry_points={
        "console_scripts": [
            "emacskeys=emacskeys.runner:main",
            "emacskeys-gui=emacskeys.gui_tool:main",
        ],
    },
    install_requires=[
        "keyboard>=0.13.5",
        "psutil>=5.8.0",
    ],
)
