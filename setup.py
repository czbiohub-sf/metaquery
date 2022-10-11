#from distutils.core import setup
from setuptools import setup

setup(name='metaquery',
      version='1.0.0',
      description='MetaQuery Query Sequence Abundance',
      url='https://github.com/czbiohub/metaquery',
      author='Chunyu Zhao and Stephen Nayfach',
      author_email='chunyu.zhao@czbiohub.org',
      license='MIT',
      packages=['metaquery', 'metaquery/src'],
      install_requires=[
        'biopython >= 1.79',
        'numpy',
      ],
      dependency_links=[],
      entry_points={
        'console_scripts': [
          'metaquery = metaquery.__main__:main'
        ]
      },
      zip_safe=False
)
