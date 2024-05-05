import setuptools

name = "aze"

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

with open("README.md", "r") as fh:
    long_description = fh.read()

version_file = "{}/version.py".format(name)
with open(version_file) as fi:
    vs = {}
    exec(fi.read(), vs)
    __version__ = vs["__version__"]


scripts = [
    "az-brute-add-app-secret",
    "az-brute-passwords",
    "az-brute-usernames",
    "az-brute-service-subdomains",
    "az-brute-blob-containers",
    "az-download-blob",
    "az-download-deployment-template",
    "az-get-login-info",
    "az-get-tenant-domains",
    "az-get-tenant-id",
    "az-inspect-token",
    "az-list-administrative-unit-members",
    "az-list-administrative-unit-role-members",
    "az-list-blobs",
    "az-list-subscriptions",
    "az-list-role-assignment",
    "az-list-sp-app-role-assignment",
    "az-list-user-memberof",
    "az-list-vm-extensions",
    "az-list-vm-permissions",
    "az-login-with-token",
    "az-search-token-in-cache",
    "az-show-ad-role",
    "az-show-administrative-unit",
    "az-whoami",
]

console_scripts = [
    "{} = {}.{}:main".format(script, name, script.replace("-", "_"))
    for script in scripts
]

setuptools.setup(
    name="zer1t0-aze",
    version=__version__,
    author="Eloy Pérez González",
    url="https://gitlab.com/Zer1t0/aze",
    description="Enhance azure cli",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    install_requires=requirements,
    entry_points={
        "console_scripts": console_scripts,
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    ],
)
