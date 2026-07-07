"""Setup script for RAG System."""
from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / 'README.md'
long_description = readme_file.read_text() if readme_file.exists() else ''

# Read requirements
requirements_file = Path(__file__).parent / 'requirements.txt'
requirements = []
if requirements_file.exists():
    requirements = [
        line.strip()
        for line in requirements_file.read_text().splitlines()
        if line.strip() and not line.startswith('#')
    ]

setup(
    name='rag-system',
    version='1.0.0',
    author='Your Name',
    author_email='your.email@example.com',
    description='Advanced RAG System for PDF Q&A with Multi-Agent Support',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/rag-system',
    packages=find_packages(exclude=['tests', 'tests.*', 'notebooks', 'deployment']),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    python_requires='>=3.10',
    install_requires=requirements,
    extras_require={
        'dev': [
            'pytest>=8.1.1',
            'pytest-cov>=5.0.0',
            'black>=24.3.0',
            'flake8>=7.0.0',
            'isort>=5.13.2',
            'mypy>=1.9.0',
        ],
        'docs': [
            'mkdocs>=1.5.3',
            'mkdocs-material>=9.5.18',
        ],
    },
    entry_points={
        'console_scripts': [
            'rag-setup=scripts.setup_db:main',
            'rag-upload=scripts.bulk_upload:main',
            'rag-benchmark=scripts.benchmark:main',
            'rag-cleanup=scripts.cleanup:main',
        ],
    },
    include_package_data=True,
    package_data={
        '': ['*.json', '*.yaml', '*.yml', '*.sql'],
    },
    zip_safe=False,
    keywords='rag retrieval-augmented-generation nlp llm openai langchain pdf qa chatbot',
    project_urls={
        'Bug Reports': 'https://github.com/yourusername/rag-system/issues',
        'Source': 'https://github.com/yourusername/rag-system',
        'Documentation': 'https://github.com/yourusername/rag-system/docs',
    },
)