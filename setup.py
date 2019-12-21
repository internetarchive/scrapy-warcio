from setuptools import setup, find_packages

with open('README.md') as rfh:
    long_description = rfh.read()

setup(
    author='Steve Sisney',
    author_email='steve@archive.org',
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    data_files=[('', ['data/middlewares.py', 'data/settings.yml'])],
    description='Scrapy WARC I/O',
    install_requires=['python-magic', 'pyyaml', 'scrapy', 'warctools'],
    long_description=long_description,
    long_description_content_type="text/markdown",
    name='scrapy-warcio',
    packages=find_packages(),
    tests_require=['pytest'],
    url='https://github.com/internetarchive/scrapy-warcio',
    version='0.0.7',
    zip_safe=False
)
