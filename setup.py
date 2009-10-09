"""A/B Testing for Django

django-lean allows you to perform split-test experiments on your users.
In brief, this involves exposing 50% of your users to one implementation 
and 50% to another, then comparing the performance of these two groups 
with regards to certain metrics.
"""

from distutils.core import setup

description, long_description = __doc__.split('\n\n', 1)

setup(
    name='django-lean',
    version='0.1',
    author='Akoha, Inc.',
    description=description,
    long_description=long_description,
    license='BSD',
    platforms=['any'],
    url='http://bitbucket.org/akoha/django-lean/wiki/Home',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audiencee :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    packages=['experiments',
        'experiments.management',
        'experiments.management.commands',
        'experiments.templatetags',
        'experiments.migrations',
        'experiments.tests',
        'experiments.tests.data',
        ],
    package_data={
       'experiments': ['templates/experiments/*.html'],
       'experiments.tests': ['data/*.json']
       },
    install_requires=["django", "beautifulsoup", "mox"],
    )
