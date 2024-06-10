# source https://medium.com/@calebjuma27/converting-from-wgs84-to-etrs89-b51157d79c70
import numpy as np
import pyproj


def cartesian_3D_from_lon_lat(long_degrees, lat_degrees, elevation_metres):
    geocent_cartesian_3D = pyproj.Proj(
        proj='geocent', ellps='WGS84', datum='WGS84')
    geographic_latlon = pyproj.Proj(
        proj='latlong', ellps='WGS84', datum='WGS84', radians=False)
    # x_coord,y_coord,z_coord=pyproj.transform(geographic_latlon,geocent_cartesian_3D,long_degrees,lat_degrees,elevation_metres,radians=False)
    transformer = pyproj.Transformer.from_proj(
        geographic_latlon, geocent_cartesian_3D, always_xy=True)
    x_coord, y_coord, z_coord = transformer.transform(
        xx=long_degrees, yy=lat_degrees, zz=elevation_metres)

    return x_coord, y_coord, z_coord


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


def lon_lat_from_cartesian_3D(x_coord, y_coord, z_coord):
    """
    built in datums:WGS84, GGRS87, NAD38, NAD27, potsdam, carthage, hermannskogel, ire65, nzgd49, OSGB336.
    built in ellipsoids: GRS80,airy,bessel,clrk66,intl,WGS60,WGS66,WGS72,WGS84,sphere
    """
    geocent_cartesian_3D = pyproj.Proj(
        # ETRS utilises the GRS80 ellipsoid. Unfortunately ETRS89 datum is not inbuilt
        proj='geocent', ellps='GRS80', datum='WGS84')
    geographic_latlon = pyproj.Proj(
        proj='latlong', ellps='GRS80', datum='WGS84', radians=False)
    # long_degrees, lat_degrees, elevation_metres = pyproj.transform(geocent_cartesian_3D, geographic_latlon, x_coord, y_coord, z_coord)
    transformer = pyproj.Transformer.from_proj(
        geocent_cartesian_3D, geographic_latlon, always_xy=True)
    long_degrees, lat_degrees, elevation_metres = transformer.transform(
        xx=x_coord, yy=y_coord, zz=z_coord)
    return long_degrees, lat_degrees, elevation_metres


def test_original_docs():
    point_WGS = {"point_1": [13.2800773632584, 52.5590577266679, 52]}
    x, y, z = cartesian_3D_from_lon_lat(
        point_WGS["point_1"][0], point_WGS["point_1"][1], point_WGS["point_1"][2])
    print(x, y, z)

    new_station, new_velocity = ITRF2014_ETRF2014(
        x_coord=x, y_coord=y, z_coord=z, ITRF_epoch=2023.02, x_velocity=0, y_velocity=0, z_velocity=0, ETRF_epoch=2023.02)
    print(*new_station)

    long, lat, elev = lon_lat_from_cartesian_3D(
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


def main():
    test_original_docs()
    # test_my_implementaion()


# Run the main function when the script is executed
if __name__ == "__main__":
    main()
