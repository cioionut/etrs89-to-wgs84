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
    # define transformer
    transformer = pyproj.Transformer.from_crs(
        f"EPSG:{source_refsys_epsg}", f"EPSG:{target_refsys_epsg}",
        always_xy=True,
        allow_ballpark=False
    )
    print(f"Transform from EPSG:{source_refsys_epsg} to EPSG:{target_refsys_epsg} with accuracy: {transformer.accuracy}")
    # iterate over points
    new_points = []
    for point in coords:
        if len(point) > 2:
            lon, lat, _alt = point[0], point[1], point[2]
        else:
            lon, lat, _alt = point[0], point[1], alt

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



def etrf2000_to_itrf2020_shape(poly_gdf: gpd.GeoDataFrame, etrf2000_epoch: float, itrf2020_epoch: float):
    # extract coords
    coords = extract_coords(poly_gdf)
    new_poly_gdf = gpd.GeoDataFrame()

    # Define the coordinate systems
    etrf2000 = 7930  # ETRF2000 - Cartesian 3D CS (geocentric) https://epsg.io/7930
    itrf2020 = 9988  # ITRF2020 - Cartesian 3D CS (geocentric) https://epsg.io/9988
    etrf2000_crs = pyproj.CRS.from_user_input(etrf2000)
    # etrf2000_crs = pyproj.CRS.from_proj4(f"+proj=geocent +ellps=GRS80 +units=m +no_defs +type=crs +to_frame=ETRF2000 @ {etrf2000_epoch}")
    itrf2020_crs = pyproj.CRS.from_user_input(itrf2020)
    print(etrf2000_crs.to_proj4())

    # define transformer
    etrf2014_to_itrf2020 = pyproj.Transformer.from_crs(etrf2000_crs, itrf2020_crs,
        always_xy=True,
        allow_ballpark=False
    )
    itrf2020_to_itrf2020 = pyproj.Transformer.from_crs(itrf2020_crs, itrf2020_crs,
        always_xy=True,
        allow_ballpark=False
    )
    print(f"Transform from etrf2000 EPSG:{etrf2000} to itrf2020 EPSG:{itrf2020} with accuracy: {etrf2014_to_itrf2020.accuracy}")
    # iterate over points
    new_points = []
    for point in coords:
        x1, y1, z1 = point[0], point[1], point[2]
        # transform in the same epoch, main reason, do the same steps like https://epncb.oma.be/_productsservices/coord_trans/index.php#results
        # x2, y2, z2, _ = etrf2014_to_itrf2020.transform(xx=x1, yy=y1, zz=z1, tt=etrf2000_epoch)
        # x, y, z, _ = itrf2020_to_itrf2020.transform(xx=x2, yy=y2, zz=z2, tt=itrf2020_epoch)
        x, y, z, _ = etrf2014_to_itrf2020.transform(xx=x1, yy=y1, zz=z1, tt=itrf2020_epoch)
        new_points.append([x, y, z])

    if len(new_points) > 3:
        new_poly = Polygon(new_points)
        new_poly_gdf.set_geometry([new_poly], inplace=True, crs=f"EPSG:{itrf2020}")
    else:
        new_poly = Point(new_points[0])
        new_poly_gdf.set_geometry([new_poly], inplace=True, crs=f"EPSG:{itrf2020}")
    
    return new_poly_gdf


def pyproj_transform_and_save(poly_gdf: gpd.GeoDataFrame, height: float,
                            source_refsys_epsg: int, target_refsys_epsg: int,
                            output_file_type: str, destination_path: str,
                            source_epoch: float, target_epoch: float):
    # new_poly_gdf = etrf2000_to_itrf2020_shape(
    #     poly_gdf, source_epoch, target_epoch)
    new_poly_gdf = pyproj_transform_shape(
        poly_gdf, height, source_refsys_epsg, target_refsys_epsg, target_epoch)
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
    area_id = 50132  # scari rulante Universitate
    # area_id = 229896  # scari rulante Universitate
    # area_id = "bucu00rou"  # Antena Facultatea Constructii
    # county_id = 403  # Bucuresti
    county_id = 289  # Bucuresti
    admin_unit_id = 129745  # Bucuresti, Sector 3
    # admin_unit_id = 179169  # Bucuresti, Sector 3
    # admin_unit_id = "tei"

    # set epoch of observations
    source_epoch = 2010.00
    target_epoch = 2022.00

    # reference system
    # source_refsys = 4258
    # source_refsys = 9059  # ETRF89
    # source_refsys = 9067  # ETRF2000
    # source_refsys = 7930  # ETRF2000 - Cartesian 3D CS (geocentric) https://epsg.io/7930
    source_refsys = 7931  # ETRF2000 - Ellipsoidal 3D CS https://epsg.io/7931

    # source_refsys = 9069  # ETRF2014
    # source_refsys = 8401  # ETRF2014 - Cartesian 3D CS (geocentric) https://epsg.io/8401

    # target_refsys = 4258  # ETRS89
    # target_refsys = 9059  # ETRF89
    # target_refsys = 9067  # ETRF2000
    # target_refsys = 7930  # ETRF2000 - Cartesian 3D CS (geocentric) https://epsg.io/7930
    # target_refsys = 8401  # ETRF2014 - Cartesian 3D CS (geocentric) https://epsg.io/8401
    # target_refsys = 9755  # wgs84 latest - https://en.wikipedia.org/wiki/World_Geodetic_System
    # target_refsys = 9000  # ITRF2014
    # target_refsys = 7789  # ITRF2014 - Cartesian 3D CS (geocentric) https://epsg.io/7789
    target_refsys = 9990  # ITRF2020 - Geographic 2D
    # target_refsys = 9988  # ITRF2020 - Cartesian 3D CS (geocentric) https://epsg.io/9988
    # target_refsys = 10606  # wgs84 G2296 == ITRF2020 - Geographic 2D

    # define data directories
    source_data_dir = os.path.join(
        'data', 'convert_transdatro', str(county_id), str(admin_unit_id), str(source_refsys))
        # 'data', 'from_euref', str(county_id), str(admin_unit_id), str(source_refsys))
    destination_data_dir = os.path.join(
        'data', 'convert_pyproj', str(county_id), str(admin_unit_id), str(target_refsys))

    # read file
    source_path = os.path.join(source_data_dir, f"{area_id}")
    # source_path = os.path.join(source_data_dir, f"{area_id}.geojson")
    poly_gdf = gpd.read_file(source_path)
    # print(poly_gdf.crs)

    assert (isinstance(poly_gdf, gpd.GeoDataFrame))
    # assert (str(source_refsys) == str(poly_gdf.crs).split(':')[1])

    # convert
    height = 112  # assume height
    output_file_type = 'shp'
    # output_file_type = 'geojson'

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
            source_epoch=source_epoch,
            target_epoch=target_epoch,
        )
    else:
        raise ValueError("Unimplemeted")


if __name__ == "__main__":
    main()
