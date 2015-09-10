from setuptools import setup

setup(
    name='Crawler',
    version='0.1',
    long_description=__doc__,
    packages=['crawler'],
    include_package_data=True,
    zip_safe=False,
    install_requires=open("requirements.txt").readlines()
)
