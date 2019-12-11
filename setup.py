from setuptools import setup, find_packages

setup(
    author='Steve Sisney',
    author_email='steve@archive.org',
    data_files=[('', 'settings.yml')],
    description='Scrapy WARC I/O',
    install_requires=['python-magic', 'pyyaml', 'scrapy', 'warctools'],
    name='scrapy_warcio',
    packages=find_packages(),
    url='https://github.com/internetarchive/scrapy_warcio',
    version='0.0.1',
    zip_safe=False
)
