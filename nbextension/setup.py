import setuptools
from glob import glob

setuptools.setup(
    name="noteboard-extension",
    version='0.1.0',
    url="https://github.com/yuvipanda/noteboard",
    author="Yuvi Panda",
    description="Simple Jupyter extension to emit events about current notebooks to a noteboard server",
    data_files=[
        ('share/jupyter/nbextensions/noteboard', glob('*.js'))
    ],
    packages=setuptools.find_packages()
)
