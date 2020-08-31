from setuptools import setup

setup(
    name='kishi',
    url='https://github.com/shunjuu/Kishi',
    author='Kyrielight',
    packages=['kishi'],
    install_requires=[
        'ayumi @ git+https://github.com/shunjuu/Ayumi',
        'requests',
    ],
    version='0.1',
    license='MIT',
    description='Anilist Userlist Fetcher.'
)