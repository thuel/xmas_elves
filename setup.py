from setuptools import setup, find_packages

def readme():
    with open('README.rst') as f:
        return f.read()

setup(name='xmas_elves',
      version='0.1',
      description='Randomly assign all persons of a group to one of the other persons as their x-mas elves.',
      long_description=readme(),
      url='',
      author='Lukas Steffen', 
      author_email='lukas@steffen-steffen.ch', 
      license='MIT', 
      install_requires=[
        'argparse',
        'logging',
        'networkx',
        'openpyxl',
      ],
      dependency_links=[
          
      ],
      packages=find_packages(),
      zip_safe=False,
      entry_points={
        'console_scripts': [
          'xmaselves = xmas_elves.xmaselves:main'
        ]
      },
      data_files=[
          
      ]
     )

