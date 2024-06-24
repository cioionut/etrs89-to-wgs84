import math
import os
import pathlib

# third party libs
import pyproj
import geopandas as gpd
from shapely.geometry import Polygon

# local
from utils import ensure_path_exists, extract_coords
from pytransdatro import TransRO


def stereo70_to_etrs89_with_gridfile(x: float, y: float, z: float, grid_file_path: str) -> tuple[float, float, float]:
    """ Convert from EPSG:3844 to EPSG:4258 """
    stereo70 = pyproj.Proj(
        f"+proj=sterea +lat_0=46 +lon_0=25 \
    +k=0.99975 +x_0=500000 +y_0=500000 +ellps=krass \
    +nadgrids={grid_file_path} +units=m +no_defs ")
    # https://epsg.io/4258
    etrs89 = pyproj.Proj("EPSG:4258")

    transformer = pyproj.Transformer.from_proj(
        stereo70, etrs89, always_xy=True)
    lon, lat, alt = transformer.transform(xx=x, yy=y, zz=z)

    return lat, lon, alt


def stereo70_to_etrs89_with_pytransdatro(t: TransRO, north: float, east: float, height: float = None):
    h = None
    if height is None:
        lat, lon = t.st70_to_etrs89(n=north, e=east)
    else:
        lat, lon, h = t.st70_to_etrs89(north, east, height)

    return math.degrees(lat), math.degrees(lon), h


def stereo70_to_etrs89_shape(poly_gdf: gpd.GeoDataFrame, height: float, target_refsys_epsg: int):
    # convert using PyTransdatRo
    t = TransRO()

    new_poly_gdf = gpd.GeoDataFrame()

    # extract coords
    stereo70_coords = extract_coords(poly_gdf)

    # iterate over points
    new_points = []
    for stereo70 in stereo70_coords:
        east, north = stereo70[0], stereo70[1]
        # convert point
        lat, lon, alt = stereo70_to_etrs89_with_pytransdatro(
            t=t,
            north=north,
            east=east,
            height=height)
        new_points.append([lon, lat])

    new_poly = Polygon(new_points)
    new_poly_gdf.set_geometry([new_poly], inplace=True,
                              crs=f"EPSG:{target_refsys_epsg}")
    return new_poly_gdf


def stereo70_to_etrs89_and_save(poly_gdf: gpd.GeoDataFrame, height: float, target_refsys_epsg: int, output_file_type: str, destination_path: str):
    new_poly_gdf = stereo70_to_etrs89_shape(
        poly_gdf, height, target_refsys_epsg)
    # write data to disk
    if output_file_type == 'geojson':
        new_poly_gdf.to_file(destination_path,
                             driver="GeoJSON", drop='crs')
    else:
        new_poly_gdf.to_file(destination_path, driver="ESRI Shapefile")


def main():
    ############
    # settings #
    ############
    area_id = 229896  # scari rulante Universitte
    county_id = 403  # Bucuresti
    admin_unit_id = 179169  # Bucuresti, Sector 3
    refsys = 3844

    target_refsys = 4258  # ETRS89
    # target_refsys = 9059  # ETRF89
    # target_refsys = 9067  # ETRF2000
    # target_refsys = 9755  # wgs84 latest - https://en.wikipedia.org/wiki/World_Geodetic_System
    # target_refsys = 9000  # ITRF2014
    # target_refsys = 9990  # ITRF2020

    # define data directories
    ancpi_data_dir = os.path.join(
        'data', 'from_ANCPI', str(county_id), str(admin_unit_id), str(refsys))
    grid_file_path = pathlib.Path(os.path.join(
        'data', 'stereo70_etrs89A.gsb')).resolve()
    conversion_data_dir = os.path.join(
        'data', 'convert_transdatro', str(county_id), str(admin_unit_id), str(target_refsys))

    # read file
    source_path = os.path.join(ancpi_data_dir, f"{area_id}.json")
    poly_gdf = gpd.read_file(source_path)
    assert (isinstance(poly_gdf, gpd.GeoDataFrame))

    # convert from Stereo70  to ETRS89, more precise
    # convert from EPSG:3844 to EPSG:9067 (etrf2000)
    # convert from EPSG:3844 to EPSG:4258 (?)

    height = 64  # assume height
    conversion_data_dir = os.path.join(conversion_data_dir, f"{area_id}")
    ensure_path_exists(conversion_data_dir)
    destination_path = os.path.join(
        conversion_data_dir, f"{area_id}.shp")
    stereo70_to_etrs89_and_save(
        poly_gdf=poly_gdf,
        height=height,
        target_refsys_epsg=target_refsys,
        output_file_type='shp',
        destination_path=destination_path
    )
    return

    # iterate over points
    height = 64  # assume height
    # extract coords
    stereo70_coords = extract_coords(poly_gdf)
    for stereo70 in stereo70_coords:
        east, north = stereo70[0], stereo70[1]
        break
    print(east, north)
    lat, lon, alt = stereo70_to_etrs89_with_gridfile(
        x=east,
        y=north,
        z=height,
        grid_file_path=grid_file_path
    )
    alt = 112
    if height == alt:
        raise ValueError(
            "Please adjust manually the altitude, the conversion only works in 2d")
    print(lat, lon, alt)

    # convert using PyTransdatRo
    t = TransRO()
    lat, lon, alt = stereo70_to_etrs89_with_pytransdatro(
        t=t,
        north=north,
        east=east,
        height=height
    )
    print(lat, lon, alt)
    # http://geo-spatial.org/transdatonline/
    # 44.43571077216;26.10206401747


if __name__ == "__main__":
    main()
