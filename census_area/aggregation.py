from core import *
from __init__ import *
from lodes import *
from variables import *
from shapely.geometry import LineString
from shapely.geometry import Polygon
from shapely.geometry import Point


#test example of geometry
# fname = 'census_area/census_area/water_district_boundary_sample.geojson'
# with open(fname) as infile:
#     my_shape_geojson = json.load(infile)

# Geometry should be a water district json file

class reaggregagion(object):
    '''
    census_API_key is the API key
    target_variable is the variable we need to calculate
    geometry should be a water district json file      
    type of statistic can be : count, per_capita, per_household.  
    type of aggregation can be: count : sum, per_capita/ per_household:  average.
    year is the year of the census
    '''
    import json
    from math import sqrt
    import requests
    import numpy as np
        
    def variable_reaggregagion(self, census_API_key, target_variable, geometry, type_of_statistic, year):

 
        c = Census(census_API_key, year = year)
        features = []
        MoE_variable = target_variable[0: len(target_variable) - 1] + 'M'
        pop_variable = 'B01003_001E'
        household_variable = 'B08201_001E'
        
        census_geo_var = c.acs5.geo_tract(('NAME', pop_variable, household_variable, target_variable, MoE_variable), geometry['features'][0]['geometry'])
        weight = {}
        population, moe_square= 0, 0
        variables = []
        total_household = 0
        for tract_geojson, tract_data, wei in census_geo_var:
            points = []
            for point in tract_geojson['geometry']['coordinates'][0]:
                points.append((point))
            tract_area = Polygon(points).area
            weight_id = tract_data['tract']
            weight[weight_id] = {}
            weight[weight_id]['area_in_tract'] =  tract_area
            # population of the census tract area
            weight[weight_id]['population'] = tract_data[pop_variable]
            
            weight[weight_id]['geometry'] =  Polygon(points)
            # areal_weight : the percentage of the intersect area 
            weight[weight_id]['areal_weight'] = wei
            # population_intersect is calculated based on areal weight. we assume that the population is evenly distributed .
            weight[weight_id]['popu_intersect'] = wei * tract_data[pop_variable]
            
            # household_intersect is calculated based on areal weight. We assume that the houses are evenly distributed.
            weight[weight_id]['household_intersect'] = tract_data[household_variable] * wei
            
            # variable_whole is the statistics of the census tract.
            
            weight[weight_id]['variable_whole'] = tract_data[target_variable]
            # calculating the whole population
            population += weight[weight_id]['popu_intersect']
            # moe_square += tract_data[MoE_variable] ** 2
            # calculating the total household
            total_household += weight[weight_id]['household_intersect']
            
        # calclate the population weight and the household weight in another for loop:            
        for wei_ids in weight:
        
            weight[wei_ids]['popul_weight'] = weight[wei_ids]['popu_intersect'] / population
            weight[wei_ids]['household_weight'] = weight[wei_ids]['household_intersect'] / total_household
    
    
        # calculate the statistic in a new for loop.
        
            # calculate a simple average in this for loop:
            # multiply population weight and areal weight
        
            # type of statistics:
        if type_of_statistic == 'count':
            type_of_aggregation = 'sum'
            for wei_ids in weight:
                weight[wei_ids]['variable_intersection'] = weight[wei_ids]['variable_whole'] * weight[wei_ids]['areal_weight']
        elif type_of_statistic == 'per_capita':
            type_of_aggregation = 'average'
            for wei_ids in weight:
                weight[wei_ids]['variable_intersection'] = weight[wei_ids]['variable_whole'] * weight[wei_ids]['popul_weight']
        elif type_of_statistic == 'per_household':
            type_of_aggregation = 'average'
            for wei_ids in weight:
                weight[wei_ids]['variable_intersection'] = weight[wei_ids]['variable_whole'] * weight[wei_ids]['household_weight']
        else:
            raise ValueError('incorrect type_of_statistic')
            
        # label of the target
        url = 'https://api.census.gov/data/' + str(year) + '/acs/acs5/variables.json'
        resp = requests.request('GET', url)
        aff1y = json.loads(resp.text)
        affkeys = np.array(list(aff1y['variables'].keys()))
        
        
        average, total_sum = 0, 0    
        if type_of_aggregation == 'sum':
            for wei_ids in weight:
                total_sum += weight[wei_ids]['variable_intersection']
            return (type_of_statistic, type_of_aggregation, total_sum, aff1y['variables'][target_variable]['label'])
        
        
        if type_of_aggregation == 'average':
            for wei_ids in weight:
                average += weight[wei_ids]['variable_whole'] *  weight[wei_ids]['popul_weight'] * weight[wei_ids]['areal_weight']
            return (type_of_statistic, type_of_aggregation, average, aff1y['variables'][target_variable]['label'])
           

        return
        
        # if type_of_aggregation == 'moe_sum':
        #     moe = sqrt(moe_square)
        #     return moe
        # else:
        #     raise ValueError('incorrect type_of_aggregation')
        
#print(reaggregagion().variable_reaggregagion('API KEY', 'B19301_001E', my_shape_geojson, 'per_capita', 1883))