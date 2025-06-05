from dagster import Definitions, load_assets_from_package

from . import assets

defs = Definitions(
  assets=load_assets_from_package(package=assets),
  jobs=[],
)