import struct
from dataclasses import dataclass, field
from typing import Optional, Type, Union

from beltzer.tables import table_lookup


def load(template_num: Union[str, float], data: bytes):
    cls = f"Template{str(template_num).replace('.', '_')}"
    return globals()[cls].load(data)

@dataclass
class Template3_0:
    shape_of_earth: int
    scale_factor_of_radius_of_spherical_earth: int
    scale_value_of_radius_of_spherical_earth: int
    scale_factor_of_major_axis_of_oblate_spheroid_earth: int
    scale_value_of_major_axis_of_oblate_spheroid_earth: int
    scale_factor_of_minor_axis_of_oblate_spheroid_earth: int
    scale_value_of_minor_axis_of_oblate_spheroid_earth: int
    num_points_along_parallel: int
    num_points_along_meridian: int
    basic_angle_initial_production_domain: int
    subdivisions_of_basic_angle: int
    latitude_of_first_grid_point: int
    longitude_of_first_grid_point: int
    resolution_and_component_flags: int
    latitude_of_last_grid_point: int
    longitude_of_last_grid_point: int
    i_direction_increment: int
    j_direction_increment: int
    scanning_mode: int
    list_num_points_along_each_merdian_or_parallel: bytes

    @classmethod
    def load(cls, data: bytes) -> "Template3_0":
        return cls(
            shape_of_earth=data[0],
            scale_factor_of_radius_of_spherical_earth=data[1],
            scale_value_of_radius_of_spherical_earth=struct.unpack('>l', data[2:6])[0],
            scale_factor_of_major_axis_of_oblate_spheroid_earth=data[6],
            scale_value_of_major_axis_of_oblate_spheroid_earth=struct.unpack('>l', data[7:11])[0],
            scale_factor_of_minor_axis_of_oblate_spheroid_earth=data[11],
            scale_value_of_minor_axis_of_oblate_spheroid_earth=struct.unpack('>l', data[12:16])[0],
            num_points_along_parallel=struct.unpack('>l', data[16:20])[0],
            num_points_along_meridian=struct.unpack('>l', data[20:24])[0],
            basic_angle_initial_production_domain=struct.unpack('>l', data[24:28])[0],
            subdivisions_of_basic_angle=struct.unpack('>l', data[28:32])[0],
            latitude_of_first_grid_point=struct.unpack('>l', data[32:36])[0],
            longitude_of_first_grid_point=struct.unpack('>l', data[36:40])[0],
            resolution_and_component_flags=data[40],
            latitude_of_last_grid_point=struct.unpack('>l', data[41:45])[0],
            longitude_of_last_grid_point=struct.unpack('>l', data[45:49])[0],
            i_direction_increment=struct.unpack('>l', data[49:53])[0],
            j_direction_increment=struct.unpack('>l', data[53:57])[0],
            scanning_mode=data[57],
            list_num_points_along_each_merdian_or_parallel=data[58:]
        )


@dataclass
class Template4_0:
    parameter_category: int
    parameter_number: int
    type_of_generating_process: int
    background_generating_process_id: int
    analysis_or_forecast_generating_process_id: int
    hours_after_ref_time_cutoff: int
    minutes_after_ref_time_cutoff: int
    time_range_unit: int
    forecast_time: int
    type_of_first_fixed_surface: int
    scale_factor_of_first_fixed_surface: int
    scaled_value_of_first_fixed_surface: int
    type_of_second_fixed_surface: int
    scale_factor_of_second_fixed_surface: int
    scaled_value_of_second_fixed_surface: int
    template_length: int

    @classmethod
    def load(cls, data: bytes) -> "Template4_0":
        return cls(
            parameter_category=data[0],
            parameter_number=data[1],
            type_of_generating_process=data[2],
            background_generating_process_id=data[3],
            analysis_or_forecast_generating_process_id=data[4],
            hours_after_ref_time_cutoff=struct.unpack(">h", data[5:7])[0],
            minutes_after_ref_time_cutoff=data[7],
            time_range_unit=data[8],
            forecast_time=struct.unpack(">l", data[9:13])[0],
            type_of_first_fixed_surface=data[13],
            scale_factor_of_first_fixed_surface=data[14],
            scaled_value_of_first_fixed_surface=struct.unpack(">l", data[15:19])[0],
            type_of_second_fixed_surface=data[19],
            scale_factor_of_second_fixed_surface=data[20],
            scaled_value_of_second_fixed_surface=struct.unpack(">l", data[21:25])[0],
            template_length=24,
        )

    @property
    def forecast_time_unit(self) -> str:
        return table_lookup("4.4", self.time_range_unit)[0].lower()

    @property
    def level(self) -> str:
        first_surface = second_surface = None
        if self.type_of_first_fixed_surface < 255:
            level = table_lookup("4.5", self.type_of_first_fixed_surface)[0].lower()
            if self.scale_factor_of_first_fixed_surface == 0:
                if self.scaled_value_of_first_fixed_surface != 0:
                    first_surface = f"{self.scaled_value_of_first_fixed_surface} {level}"
                else:
                    first_surface = level
            else:
                first_surface = (
                    f"{self.scaled_value_of_first_fixed_surface / self.scale_factor_of_first_fixed_surface} {level}"
                )
        if self.type_of_second_fixed_surface < 255:
            level = table_lookup("4.5", self.type_of_second_fixed_surface)[0].lower()
            if self.scale_factor_of_second_fixed_surface == 0:
                second_surface = level
            else:
                second_surface = (
                    f"{self.scaled_value_of_second_fixed_surface / self.scale_factor_of_second_fixed_surface} {level}"
                )
        if first_surface:
            if second_surface:
                return f"{first_surface}-{second_surface}"
            return first_surface
        if second_surface:
            return second_surface
        return ""


@dataclass
class Template4_1(Template4_0):
    type_of_ensemble_forecast: int
    perturbation_number: int
    num_forecasts_in_ensemble: int


@dataclass
class Template4_2(Template4_0):
    derived_forecast: int
    num_forecasts_in_ensemble: int


@dataclass
class Template4_3(Template4_0):
    derived_forecast: int
    num_forecasts_in_ensemble: int
    cluster_identifier: int
    cluster_num_to_which_high_res_control_belongs: int
    cluster_num_to_which_low_res_control_belongs: int
    total_num_clusters: int
    clustering_method: int
    northern_lat_of_cluster_domain: int
    southern_lat_of_cluster_domain: int
    eastern_lon_of_cluster_domain: int
    western_lon_of_cluster_domain: int
    nc_num_forecasts_in_cluster: int
    scale_factor_of_std_dev_in_cluster: int
    scale_factor_of_distance_of_cluster_from_ensemble_mean: int
    scaled_val_of_distance_of_cluster_from_ensemble_mean: int
    list_of_nc_ensemble_forecast_nums: int


@dataclass
class Template4_4(Template4_0):
    derived_forecast: int
    num_forecasts_in_ensemble: int
    cluster_identifier: int
    cluster_num_to_which_high_res_control_belongs: int
    cluster_num_to_which_low_res_control_belongs: int
    total_num_clusters: int
    clustering_method: int
    lat_of_central_point_in_cluster_domain: int
    lon_of_central_point_in_cluster_domain: int
    radius_of_cluster_domain: int
    nc_num_forecasts_in_cluster: int
    scale_factor_of_std_dev_in_cluster: int
    scale_factor_of_distance_of_cluster_from_ensemble_mean: int
    scaled_val_of_distance_of_cluster_from_ensemble_mean: int
    list_of_nc_ensemble_forecast_nums: int


@dataclass
class Template4_5(Template4_0):
    forecast_probability_number: int
    total_num_forecast_probabilities: int
    probability_type: int
    scale_factor_of_lower_limit: int
    scaled_value_of_lower_limit: int
    scale_factor_of_upper_limit: int
    scaled_value_of_upper_limit: int


@dataclass
class Template4_6(Template4_0):
    percentile_value: int


@dataclass
class Template4_7(Template4_0):
    pass


@dataclass
class Template4_8(Template4_0):
    pass
