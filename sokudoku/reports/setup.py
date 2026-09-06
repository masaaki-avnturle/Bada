from setuptools import setup, find_packages

setup(
    name='pkggen',
    version='0.2.0',
    packages=find_packages(),
    install_requires=[
        # Add any required dependencies here
    ],
    entry_points={
        'console_scripts': [
            'pkggen = omega_script.bin.omega_script:main',
        ],
    },
)

