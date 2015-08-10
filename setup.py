from setuptools import setup, find_packages
import sys, os

version = '0.2.a'

setup(name='openid-mongodb',
      version=version,
      description="A MongoDb storage backend for the python-openid package",
      classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Topic :: Internet :: WWW/HTTP"
      ],
      keywords='openid mongodb',
      author='Ariel Backenroth',
      author_email='arielb@alumni.rice.edu',
      url='http://github.com/arielbackenroth/openid-mongodb',
      license='MIT',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      test_suite="tests.test_mongodbstore",
      install_requires=["pymongo>=3", "python-openid>=2.2.4"]
)
