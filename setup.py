import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))


runtime = set([
    "insights-core",
    "dill==0.3.2",
    "pyzmq==19.0.0",
])

develop = set([
    "flake8==3.8.3",
    "black==19.10b0",
    "pytest==5.4.3",
    "setuptools==41.6.0",
    "wheel==0.34.2",
    "IPython==7.16.1",
])

docs = set([
    "Sphinx==3.1.2",
    "sphinx_rtd_theme==0.5.0",
])


if __name__ == "__main__":
    with open(os.path.join(here, "README.md"), encoding="utf-8") as f:
        long_description = f.read()

    setup(
        name="insights-sandbox",
        version="0.1.0",
        description="bubblewrap sandbox for insights components.",
        long_description=long_description,
        long_description_content_type="text/markdown",
        url="https://github.com/RedHatInsights/insights-sandbox",
        author="Red Hat, Inc.",
        author_email="insights@redhat.com",
        packages=find_packages(),
        install_requires=list(runtime),
        package_data={"": ["LICENSE"]},
        license="Apache 2.0",
        extras_require={
            "develop": list(develop | docs),
            "docs": list(docs),
        },
        classifiers=[
            "Development Status :: 4 - Beta",
            "Intended Audience :: Developers",
            "Natural Language :: English",
            "License :: OSI Approved :: Apache Software License",
            "Programming Language :: Python",
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8"
        ],
        include_package_data=True
    )
