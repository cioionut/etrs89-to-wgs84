import os

# third party libs
import pyproj
import geopandas as gpd
from shapely.geometry import Polygon, Point

# local
from utils import ensure_path_exists, extract_coords


def pyproj_transform_shape(poly_gdf: gpd.GeoDataFrame, alt: float,
                           source_refsys_epsg: int, target_refsys_epsg: int,
                           observation_epoch: float):
    # extract coords
    coords = extract_coords(poly_gdf)
    new_poly_gdf = gpd.GeoDataFrame()

    # iterate over points
    new_points = []
    for point in coords:
        if len(point) > 2:
            lon, lat, _alt = point[0], point[1], point[2]
        else:
            lon, lat, _alt = point[0], point[1], alt

        transformer = pyproj.Transformer.from_crs(
            f"EPSG:{source_refsys_epsg}", f"EPSG:{target_refsys_epsg}",
            always_xy=True,
            allow_ballpark=False
        )
        lon, lat, __alt, _ = transformer.transform(
            xx=lon, yy=lat, zz=_alt, tt=observation_epoch)

        new_points.append([lon, lat, __alt])

    if len(new_points) > 3:
        new_poly = Polygon(new_points)
        new_poly_gdf.set_geometry([new_poly], inplace=True, crs=f"EPSG:{target_refsys_epsg}")
    else:
        new_poly = Point(new_points[0])
        new_poly_gdf.set_geometry([new_poly], inplace=True, crs=f"EPSG:{target_refsys_epsg}")
    return new_poly_gdf


def pyproj_transform_and_save(poly_gdf: gpd.GeoDataFrame, height: float,
                            source_refsys_epsg: int, target_refsys_epsg: int,
                            output_file_type: str, destination_path: str,
                            observation_epoch: float):
    new_poly_gdf = pyproj_transform_shape(
        poly_gdf, height, source_refsys_epsg, target_refsys_epsg, observation_epoch)
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
    # area_id = 229896  # scari rulante Universitate
    area_id = "bucu00rou"  # Antena Facultatea Constructii
    county_id = 403  # Bucuresti
    # admin_unit_id = 179169  # Bucuresti, Sector 3
    admin_unit_id = "tei"

    # set epoch of observations
    observation_epoch = 2003.46

    # reference system
    # source_refsys = 4258
    # source_refsys = 9059  # ETRF89
    # source_refsys = 9067  # ETRF2000
    # source_refsys = 7931  # ETRF2000 - Ellipsoidal 3D CS https://epsg.io/7931
    source_refsys = 7930  # ETRF2000 - Cartesian 3D CS (geocentric) https://epsg.io/7930
    # source_refsys = 9069  # ETRF2014

    # target_refsys = 4258  # ETRS89
    # target_refsys = 9059  # ETRF89
    # target_refsys = 9067  # ETRF2000
    # target_refsys = 7930  # ETRF2000 - Cartesian 3D CS (geocentric) https://epsg.io/7930
    # target_refsys = 9755  # wgs84 latest - https://en.wikipedia.org/wiki/World_Geodetic_System
    # target_refsys = 9000  # ITRF2014
    # target_refsys = 7789  # ITRF2014 - Cartesian 3D CS (geocentric) https://epsg.io/7789
    target_refsys = 9990  # ITRF2020

    # define data directories
    source_data_dir = os.path.join(
        # 'data', 'convert_transdatro', str(county_id), str(admin_unit_id), str(source_refsys))
        'data', 'from_euref', str(county_id), str(admin_unit_id), str(source_refsys))
    destination_data_dir = os.path.join(
        'data', 'convert_pyproj', str(county_id), str(admin_unit_id), str(target_refsys))

    # read file
    # source_path = os.path.join(source_data_dir, f"{area_id}")
    source_path = os.path.join(source_data_dir, f"{area_id}.geojson")
    poly_gdf = gpd.read_file(source_path)
    # print(poly_gdf.crs)

    assert (isinstance(poly_gdf, gpd.GeoDataFrame))
    # assert (str(source_refsys) == str(poly_gdf.crs).split(':')[1])

    # convert
    height = 112  # assume height
    output_file_type = 'shp'

    if output_file_type in ['shp', 'geojson']:
        destination_data_dir = os.path.join(destination_data_dir, f"{area_id}")
        ensure_path_exists(destination_data_dir)
        # destination_path = os.path.join(destination_data_dir, f"{area_id}.shp")
        destination_path = os.path.join(destination_data_dir, f"{area_id}.{output_file_type}")

        pyproj_transform_and_save(
            poly_gdf=poly_gdf,
            height=height,
            source_refsys_epsg=source_refsys,
            target_refsys_epsg=target_refsys,
            output_file_type='shp' if destination_path.split('.')[-1] == 'shp' else 'geojson',
            destination_path=destination_path,
            observation_epoch=observation_epoch
        )
    else:
        raise ValueError("Unimplemeted")


if __name__ == "__main__":
    main()
