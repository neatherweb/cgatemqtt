from setuptools import setup, find_packages

setup(name='cgatemqtt',
      version='0.2',
      description='MQTT gateway service for Clipsal Cbus smart home',
      url=None,
      author='Jason Neatherway',
      author_email='neatherweb@gmail.com',
      license='MIT',
      packages=find_packages(),
      install_requires=[
          'paho-mqtt'
      ],
      zip_safe=False,
      entry_points = {
          'console_scripts': ['cgatemqtt=cgatemqtt.service:main'],
      }
     )


