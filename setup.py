import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

    setuptools.setup(
        name="mtapi",
        version="0.1.1",
        author="Oleksii Pshenychnyi",
        author_email="afw@afw.net.ua",
        description="Mikrotik asynchronous API",
        long_description=long_description,
        long_description_content_type="text/markdown",
        url="https://github.com/pshenyaga/mtapi",
        packages=['mtapi'],
        classifiers=[
            "Programming Language :: Python :: 3",
            "License :: OSI Approved :: GNU GPLv3",
            "Operating System :: OS Independent",
        ],
    )
