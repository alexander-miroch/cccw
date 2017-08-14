from distutils.core import setup, Extension
from os import path

here = path.abspath(path.dirname(__file__))

setup(
    name = "CloudCoin Console Wallet",

    version = "0.1.14",

    author = "Alexander Miroch",
    author_email = "alexander.miroch@protonmail.com",

    packages = ["ccm"],

    #include_package_data = True,

    url="http://pypi.python.org/pypi/cccw/",

    scripts = ['./cccw.py'],

    # license="LICENSE.txt",
    description="Client Application for Validating CloudCoin Currency",

    # Dependent packages (distributions)
    #install_requires=[
    #    "",
    #],

    package_data = {
        'cccw': ['./cccw'],
    }

)
