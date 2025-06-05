from setuptools import find_packages, setup

setup(
    name="dagster_project",
    packages=find_packages(exclude=["dagster_project_tests"]),
    install_requires=[
        "dagster==1.10.3",
        "dagster-cloud",
        "dagster-dbt",
        "dbt-snowflake",
        "snowflake-connector-python",
        "pandas"
    ],
    extras_require={"dev": ["dagster-webserver", "pytest"]},
)