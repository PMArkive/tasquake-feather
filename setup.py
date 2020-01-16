from distutils.core import setup

setup(name='feather',
      version='0.0.1',
      description='A lightweight program for generating Markdown documentation',
      author='Jukspa',
      requires=['jinja2'],
      entry_points={
            'console_scripts': [
                'feather = feather:main',
            ],
        }
     )