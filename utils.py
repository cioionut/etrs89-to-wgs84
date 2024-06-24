import pathlib

import geopandas as gpd


def ensure_path_exists(path: str):
    pathlib.Path(path).mkdir(parents=True, exist_ok=True)


def extract_coords(geo_df: gpd.GeoDataFrame) -> list[tuple[float, float]]:
    poly = geo_df.iloc[0]['geometry']
    coords = poly.exterior.coords
    return coords
