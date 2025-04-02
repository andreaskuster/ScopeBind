from setuptools import setup, find_packages

def read_requirements():
    with open("requirements.txt", "r") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="ScopeBind",
    version="0.1.0",
    author="Andreas Kuster",
    author_email="your.email@example.com",
    description="Python bindings for USB oscilloscopes",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/andreaskuster/ScopeBind",
    packages=find_packages(),
    install_requires=read_requirements(),  # Load dependencies from requirements.txt
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
