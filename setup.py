from setuptools import setup, find_packages

with open("beltzer/__init__.py") as f:
    for line in f:
        if line.startswith('__version__'):
            version = line.split()[-1].strip('"').strip("'")

with open("README.rst") as f:
    readme = f.read()

setup(
    name="beltzer",
    version=version,
    description="Meteorological data toolkit",
    long_description=readme,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License "
    ],
    keywords="GRIB, weather, meteorology, data",
    author="Jon Oxtoby",
    author_email="jon@ox5tech.com",
    url="https://github.com/joxtoby/beltzer",
    license="MIT",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=["requests"]
)
