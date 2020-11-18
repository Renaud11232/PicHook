import setuptools


def get_long_description():
    with open("README.md", "r") as readme:
        return readme.read()


setuptools.setup(
    name="PicHook",
    version="0.1.0rc2",
    author="Renaud Gaspard",
    author_email="gaspardrenaud@hotmail.com",
    description="Discord hook that automatically sends your artworks",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/Renaud11232/PicHook",
    packages=setuptools.find_packages(),
    entry_points=dict(
        console_scripts=[
            "pic-hook=pichook.command_line:main"
        ]
    ),
    install_requires=[
        "discord.py",
        "pause",
        "croniter"
    ],
    classifiers=[
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
