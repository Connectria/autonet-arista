import os
import setuptools

with open("README.rst", "r", encoding="utf-8") as fh:
    long_description = fh.read()

here = os.path.abspath(os.path.dirname(__file__))
about = {}
with open(here + '/autonet_arista/__version__.py', 'r') as f:
    exec(f.read(), about)

install_requires = [
    'autonet-api',
    'pyeapi>=0.8.4'
]

test_requires = install_requires + [
    'pytest',
]

setuptools.setup(
    name="autonet-arista",
    version=about['__version__'],
    author="Ken Vondersaar",
    author_email="kvondersaar@connectria.com",
    description="Network device configuration abstraction API",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    url="https://github.com/Connectria/autonet_arista",
    project_urls={
        "Bug Tracker": "https://github.com/Connectria/autonet_arista",
        "Documentation": "https://connectria.github.io/autonet_arista",
    },
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Development Status :: 4 - Beta"
        "License :: Other/Proprietary License"
        "Operating System :: OS Independent",
    ],
    package_dir={"": "./"},
    packages=setuptools.find_packages(where='./'),
    python_requires=">=3.8",
    install_requires=install_requires,
    test_requires=test_requires,
    test_suite='pytest',
    exclude_package_data={'': ['*/tests/*']},
    entry_points={
        'autonet.drivers': ['eos = autonet_arista.eos.eos_driver:AristaDriver']
    }
)
