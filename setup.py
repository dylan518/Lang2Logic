from setuptools import setup, find_packages
from setuptools.command.install import install
import subprocess


class CustomInstall(install):

    def run(self):
        # Call the parent method
        install.run(self)
        # Custom post-install code to install improved-datamodel-codegen with no dependencies
        subprocess.call([
            'pip', 'install', 'improved-datamodel-codegen==1.2.1', '--no-deps'
        ])


# Read dependencies from requirements.txt
with open('requirements.txt') as f:
    required = f.read().splitlines()

# Read the long description from README.md
with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='Lang2Logic',
    version='1.2.0',
    description=
    'A package for generating, validating, and utilizing Draft-7 JSON schemas with LangChain',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Dylan Wilson',
    author_email='dylanpwilson2005@gmail.com',
    license='CC0-1.0',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: Other/Proprietary License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.11',
    ],
    keywords='language models, structured output',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    package_data={
        'Lang2Logic': ['app_data.json'],
    },
    python_requires='>=3.7, <4',
    install_requires=required,
    extras_require={
        'dev': ['check-manifest'],
        'test': ['coverage'],
    },
    project_urls={},
    cmdclass={
        'install': CustomInstall,
    },
)
