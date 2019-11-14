from setuptools import setup, find_packages

def readme():
    with open('README.rst') as f:
        return f.read()

setup(name='xmas_elves',
      version='0.1',
      description='Description here...',
      long_description=readme(),
      url='',
      author='Lukas Steffen', #Default: 'Lukas Steffen',
      author_email='lukas@steffen-steffen.ch', #Default: 'lukas@steffen-steffen.ch',
      license='MIT', #Default: MIT
      install_requires=[
        # List of modules which are imported by the project.
        # But not core modules like subprocess or os.
        'argparse',
        'logging'
      ],
      dependency_links=[
          # e.g. "git+https://bitbucket.org/thuel/mail_py.git@0.2.2#egg=mail_py-0.2.2"
      ],
      packages=find_packages(),
      zip_safe=False,
      entry_points={
        'console_scripts': [
          'xmas_elves = xmas_elves.xmas_elves:main'
        ]
      },
      data_files=[
          # e.g. ('/some/path/', 'some_file')
      ]
     )

