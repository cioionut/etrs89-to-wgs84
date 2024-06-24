import os

# third party libs
import numpy as np
import pyproj
import geopandas as gpd
from shapely.geometry import Polygon

# local
from utils import ensure_path_exists, extract_coords


def cartesian_3D_from_lon_lat_wgs84(long_degrees, lat_degrees, elevation_metres):
    geocent_cartesian_3D = pyproj.Proj(
        proj='geocent', ellps='WGS84', datum='WGS84')
    geographic_latlon = pyproj.Proj(
        proj='latlong', ellps='WGS84', datum='WGS84', radians=False)
    transformer = pyproj.Transformer.from_proj(
        geographic_latlon, geocent_cartesian_3D, always_xy=True)
    x_coord, y_coord, z_coord = transformer.transform(
        xx=long_degrees, yy=lat_degrees, zz=elevation_metres)

    return x_coord, y_coord, z_coord


def lon_lat_from_cartesian_3D_grs80(x_coord, y_coord, z_coord):
    geocent_cartesian_3D = pyproj.Proj(
        # ETRS utilises the GRS80 ellipsoid. Unfortunately ETRS89 datum is not inbuilt
        proj='geocent', ellps='GRS80', datum='WGS84')
    geographic_latlon = pyproj.Proj(
        proj='latlong', ellps='GRS80', datum='WGS84', radians=False)
    transformer = pyproj.Transformer.from_proj(
        geocent_cartesian_3D, geographic_latlon, always_xy=True)
    long_degrees, lat_degrees, elevation_metres = transformer.transform(
        xx=x_coord, yy=y_coord, zz=z_coord)
    return long_degrees, lat_degrees, elevation_metres


def ITRF2014_ETRF2014(x_coord, y_coord, z_coord, ITRF_epoch, **kwargs):

    x_velocity = kwargs.get("x_velocity", 0)
    y_velocity = kwargs.get("y_velocity", 0)
    z_velocity = kwargs.get("z_velocity", 0)
    ETRF_epoch = kwargs.get("ETRF_epoch", ITRF_epoch)

    """converts stations from one system to another. Important for the stations to have velocity information incase different epochs are used
        x_coord=x coordinate of the station
        y_coord= y coordinate of the station
        z_coord= z coordinate of the station

        x_velocity, y_velocity, z_velocity = the velocity of the station (metres per year)
        NB: x_velocity = 0,y_velocity=0 and z_velocity = 0 if ITRF_Epoch=ETRF_Epoch,
        ITRF_epoch= the date (in decimal years) of the data measurement
        ETRF_epoch= The date(in decimal years) of the data in the new system. one can go either to the past, present or future
    """

    station_point_array = np.array([x_coord, y_coord, z_coord])
    station_velocity_array = np.array([x_velocity, y_velocity, z_velocity])

    # Epoch of observation
    observation_epoch = ITRF_epoch
    # ETRS frame. apparently this variable is constant
    ETRS_F = 1989

    # Transformation parameters for ITRF2014 to ETRF 2014, epoch of observation 2010.0
    # translation
    tx_ty_tz = [0.0, 0.0, 0.0]
    # translation rate
    txa_tya_tza = [0.0, 0.0, 0.0]

    # rotation
    Rx_Ry_Rz = [1.785, 11.151, -16.170]
    # rotation rate
    Rxa_Rya_Rza = [0.085, 0.531, -0.770]

    # scalefactor
    scale_factor = 0.00*(10**-9)

    # create transformation equation

    """ NB: be careful of units
        Translations in mm, transform to m
        rotations in mas/yr, transform to rad/yr
        mas= milliarcsecond, rad=radians
        1 mas = 4.8481368E-9 rad
        or 1 rad=206264806.2471 mas
        or
        1) convert from milliarcseconds to arc seconds ( multiply by 0.001)
        2) convert from arcsecond to degrees (divide by 3600)
        3) convert from degrees to radians multiply by (pi/180) """

    # rotation matrix and transformation matrix in SI Units
    t_array = (np.array(tx_ty_tz)) / 1000  # change to metres
    scale_factor_array = np.array([scale_factor, scale_factor, scale_factor])
    rotation_rate_array = (np.array([[0, -Rxa_Rya_Rza[2], Rxa_Rya_Rza[1]], [
                           Rxa_Rya_Rza[2], 0, -Rxa_Rya_Rza[0]], [-Rxa_Rya_Rza[1], Rxa_Rya_Rza[0], 0]])) / 206264806.247

    # Helmerts equation
    station_array_transformed = np.add(station_point_array, np.add(t_array, (np.matmul(
        # can only add 2 arrays at a time
        rotation_rate_array, (station_point_array*(observation_epoch-ETRS_F))))))
    station_velocity_tranformed = np.add(
        station_velocity_array, np.matmul(rotation_rate_array, station_point_array))

    # suitable for transformng between different epochs
    station_points_ETRF2014 = np.add(station_array_transformed, np.multiply(
        station_velocity_tranformed, (ETRF_epoch-ITRF_epoch)))

    return station_points_ETRF2014, station_velocity_tranformed


def test_original_docs():
    point_WGS = {"point_1": [13.2800773632584, 52.5590577266679, 52]}
    x, y, z = cartesian_3D_from_lon_lat_wgs84(
        point_WGS["point_1"][0], point_WGS["point_1"][1], point_WGS["point_1"][2])
    print(x, y, z)

    new_station, new_velocity = ITRF2014_ETRF2014(
        x_coord=x, y_coord=y, z_coord=z, ITRF_epoch=2023.02, x_velocity=0, y_velocity=0, z_velocity=0, ETRF_epoch=2023.02)
    print(*new_station)

    long, lat, elev = lon_lat_from_cartesian_3D_grs80(
        new_station[0], new_station[1], new_station[2])
    print(long, lat, elev)
    # https://epncb.oma.be/_productsservices/coord_trans/index.php#results
    # Station_1 ITRF2014 2023.02  3781875.0154   892608.9842  5040903.8362   0.0000   0.0000   0.0000
    # Station_1 ETRF2014 2023.02  3781875.5702   892608.4333  5040903.5175   0.0000   0.0000   0.0000

    # deviation_per_year=2.5 #cm
    # period=2023-1989

    # total_deviation= deviation_per_year*period

    # print(total_deviation)
    # #comes to 85 cm


def itrf2014_to_etrf2014_lon_lat(lon, lat, elev, observation_epoch):
    x, y, z = cartesian_3D_from_lon_lat_wgs84(lon, lat, elev)
    new_station, new_velocity = ITRF2014_ETRF2014(
        x_coord=x, y_coord=y, z_coord=z,
        ITRF_epoch=observation_epoch,
        x_velocity=0, y_velocity=0, z_velocity=0,
        ETRF_epoch=observation_epoch)
    long, lat, elev = lon_lat_from_cartesian_3D_grs80(
        new_station[0], new_station[1], new_station[2])
    return long, lat, elev


def my_transform_shape(poly_gdf: gpd.GeoDataFrame, alt: float,
                       source_refsys_epsg: int, target_refsys_epsg: int,
                       observation_epoch: float):
    # extract coords
    coords = extract_coords(poly_gdf)
    new_poly_gdf = gpd.GeoDataFrame()

    # iterate over points
    new_points = []
    for point in coords:
        lon, lat = point[0], point[1]
        lon, lat, alt = itrf2014_to_etrf2014_lon_lat(
            lon, lat, alt, observation_epoch)
        new_points.append([lon, lat])

    new_poly = Polygon(new_points)
    new_poly_gdf.set_geometry([new_poly], inplace=True,
                              crs=f"EPSG:{target_refsys_epsg}")
    return new_poly_gdf


def itrs_to_etrs89_and_save(poly_gdf: gpd.GeoDataFrame, height: float,
                            source_refsys_epsg: int, target_refsys_epsg: int,
                            output_file_type: str, destination_path: str,
                            observation_epoch: float):
    new_poly_gdf = my_transform_shape(
        poly_gdf, height, source_refsys_epsg, target_refsys_epsg, observation_epoch)
    # write data to disk
    if output_file_type == 'geojson':
        new_poly_gdf.to_file(destination_path,
                             driver="GeoJSON", drop='crs')
    else:
        new_poly_gdf.to_file(destination_path, driver="ESRI Shapefile")


def convert_file():
    ############
    # settings #
    ############
    area_id = 229896  # scari rulante Universitte
    county_id = 403  # Bucuresti
    admin_unit_id = 179169  # Bucuresti, Sector 3

    # set epoch of observations
    observation_epoch = 2024.45

    # reference system
    source_refsys = 9000  # ITRF2014
    target_refsys = 9069  # ETRF2014

    # define data directories
    source_data_dir = os.path.join(
        'data', 'convert_pyproj', str(county_id), str(admin_unit_id), str(source_refsys))
    destination_data_dir = os.path.join(
        'data', 'convert_my', str(county_id), str(admin_unit_id), str(target_refsys))

    # read file
    source_path = os.path.join(source_data_dir, f"{area_id}")
    poly_gdf = gpd.read_file(source_path)
    # print(poly_gdf.crs)

    assert (isinstance(poly_gdf, gpd.GeoDataFrame))
    # assert (str(source_refsys) == str(poly_gdf.crs).split(':')[1])

    # convert
    height = 112  # assume height
    output_file_type = 'shp'

    if output_file_type == 'shp':
        destination_data_dir = os.path.join(destination_data_dir, f"{area_id}")
        ensure_path_exists(destination_data_dir)
        destination_path = os.path.join(
            destination_data_dir, f"{area_id}.shp")

        itrs_to_etrs89_and_save(
            poly_gdf=poly_gdf,
            height=height,
            source_refsys_epsg=source_refsys,
            target_refsys_epsg=target_refsys,
            output_file_type='shp',
            destination_path=destination_path,
            observation_epoch=observation_epoch
        )
    else:
        raise ValueError("Unimplemeted")


def main():
    # test_original_docs()
    convert_file()


if __name__ == "__main__":
    main()
