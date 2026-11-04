
#################################################
## GENERATE SSP DRIVERS
#################################################

## general imports
import os
import numpy as np
import xarray as xr
import pandas as pd

## specific imports
from core_fct.fct_misc import aggreg_region, load_data
from core_fct.fct_loadD import load_landuse_hist, load_RFdrivers_hist, load_landuse_scen, load_RFdrivers_scen
from core_fct.fct_loadP_av import load_all_param
from core_fct.fct_genMC import generate_config

folder_out = 'results/SSP_drivers/'
mod_region = 'RCP_5reg'

# ----------------------
# 0. Setup & parameters
# ----------------------
if not os.path.isdir(folder_out):
    os.mkdir(folder_out)

Par0 = load_all_param(mod_region)

# ----------------------
# 1. HISTORICAL
# ----------------------

## load emissions
data_in = xr.open_dataset('/OSCAR_aviation/input_data/drivers_av/emission_hist_1750_2024.nc')
For_hist = data_in.mean('scen')

## Separation of the aviation sector emissions for the different species
aircraft_sector = 'Aircraft'
vars_emissions = ['E_BC', 'E_SO2', 'E_OC', 'E_NOX', 'Eff']

var_av_dict = {}
for var in vars_emissions:
    var_av = For_hist[var].sel(sector=aircraft_sector)
    var_av_dict[f'{var}_av'] = var_av

For_hist = For_hist.sum('sector')

for var in vars_emissions:
    For_hist[f'{var}_av'] = var_av_dict[f'{var}_av']
    if var != 'Eff':
        For_hist[var] = For_hist[var] - var_av_dict[f'{var}_av']

## List all species
tt_var = list(For_hist.data_vars)
for var in var_av_dict:
    if var not in tt_var:
        tt_var.append(var)

## Warning: the input data does not specify any regions, therefore:
for var_name in tt_var: 
    if var_name in For_hist:
        test = For_hist[var_name] / 6
        test_expanded = test.expand_dims(dim={"reg_land": 6})
        test_replicated = test_expanded.broadcast_like(xr.DataArray(np.arange(6), dims="reg_land"))
        For_hist[var_name] = test_replicated

## load LULCC
TMP = load_landuse_hist(mod_region, ['LUH2'], LCC='gross').sel(data_LULCC='LUH2', drop=True)
For_hist = xr.merge([For_hist, TMP])

## Offline forcing data (load RF drivers & remove old RF_contr (empty))
TMP = load_RFdrivers_hist().sel(data_RF_contr='ICAO', data_RF_solar='CMIP6', data_RF_volc='CMIP6', drop=True)
TMP = TMP.drop_vars('RF_contr')

## Fuels : from ACACIA for O3t, from (Lee et al., 2021) for H20s and Contrails
Fuel_for_RF = xr.open_dataset('/OSCAR_aviation/input_data/drivers_av/fuel_scaling_factor_for_rf_av_hist_1750_2024.nc')

# Merge land use and external aviation forcings
For_hist = xr.merge([For_hist, Fuel_for_RF, TMP])

#--- Emissions set to 0 in NP_evt_ltag.py ---# 

## load atmospheric concentrations
TMP = load_data('concentrations_CMIP6').sel(region='Globe', drop=True)
for VAR in ['CO2', 'CH4', 'N2O', 'Xhalo']:
    For_hist['D_'+VAR] = TMP[VAR] - Par0[VAR+'_0']

## missing drivers
For_hist['Eluc'] = 0*For_hist['Eff']
For_hist['E_N2O'] = 0*For_hist['Eff']
For_hist['E_Xhalo'] = 0*For_hist['D_Xhalo']

For_hist = For_hist.sel(year=slice(1750, 2024)).fillna(0.)
if __name__ == '__main__':
    For_hist.to_netcdf(folder_out + 'For_hist_SSP.nc', encoding={var:{'zlib':True, 'dtype':np.float32} for var in For_hist})

# ----------------------
# 2. SCENARIOS
# ----------------------

## Reference scenario for the integration of LTAG scenarios
id_scen = 'SSP3-7.0'
year_end = 2070

## load emissions
import_scen = xr.open_dataset('/OSCAR_aviation/input_data/drivers_av/emission_ssp_2025_2100.nc')
df_LTAG = xr.open_dataset('/OSCAR_aviation/input_data/drivers_av/emission_ltag_av_2025_2070.nc')

## LTAG scenarios - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -  
## Replace aircraft sector emissions for "E_CO2", "E_BC", "E_NOX", "E_SO2" 
## Generate a new dataset using the same SSP baseline
ds = import_scen.sel(scen=id_scen).interp(year=df_LTAG.year.values)
suffixes = ['F0-Low', 'F1-Low', 'F2-Low', 'F3-Low', 'F0-Medium', 'F1-Medium', 'F2-Medium', 'F3-Medium', 'F0-High', 'F1-High', 'F2-High', 'F3-High']
scen_names = [f"{id_scen}_{suffix}" for suffix in suffixes]
ds_repeated = xr.concat([ds] * len(suffixes), dim='scen')
For_scen = ds_repeated.assign_coords(scen=('scen', scen_names))

df_remapped = df_LTAG.assign_coords(
    scen=[f"{id_scen}_{s}" for s in df_LTAG.scen.values])

vars_to_replace = ["Eff", "E_BC", "E_NOX", "E_SO2"]
for var in vars_to_replace:
    if var in df_remapped and var in For_scen:
        For_scen[var].loc[dict(sector="Aircraft")] = df_remapped[var].squeeze()

## End - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

tt_var = list(For_scen.data_vars)
for var_name in tt_var: 
    if var_name in For_scen:
        test = For_scen[var_name] / 6
        test_expanded = test.expand_dims(dim={"reg_land": 6})
        test_replicated = test_expanded.broadcast_like(xr.DataArray(np.arange(6), dims="reg_land"))
        For_scen[var_name] = test_replicated
For_scen = xr.concat([For_scen, For_scen.sel(year=year_end).assign_coords(year=2300)], dim='year')

import_Eluc_EN20_1 = aggreg_region(load_data('emissions_ScenarioMIP'), mod_region, old_axis='region', dataset='ScenarioMIP')
ds_import_Eluc_EN20 = import_Eluc_EN20_1.sel(scen=id_scen)
ds_import_Eluc_EN20_repeted = xr.concat([ds_import_Eluc_EN20] * len(suffixes), dim='scen')
import_Eluc_EN20 = ds_import_Eluc_EN20_repeted.assign_coords(scen=('scen', scen_names))
TMP_E = import_Eluc_EN20[['E_N2O', 'Eluc']].dropna('year', how='all')
For_scen.update(TMP_E.interp(year=For_scen.year))

## correction: non-CO2 emissions from FF&I decrease to 0, while those from LUC stay constant
sectors_LU = ['Forest Burning', 'Grassland Burning', 'Peat Burning'] + ['Agricultural Waste Burning', 'Agriculture']
for var in For_scen.variables:
    if (var not in For_scen.coords)  and  (var not in ['E_N2O', 'Eluc']):
        For_scen[var].loc[{'sector':[sec for sec in For_scen.sector.values if sec not in sectors_LU], 'year':2300}] = 0.

## Separation of the aviation sector emissions for the different species
vars_emissions = ['E_BC', 'E_SO2', 'E_OC', 'E_NOX', 'Eff']
aircraft_sector = 'Aircraft'

var_av_dict = {
    f"{var}_av": For_scen[var].sel(sector=aircraft_sector)
    for var in vars_emissions}

For_scen = For_scen.sum('sector')

for var in vars_emissions:
    For_scen[f"{var}_av"] = var_av_dict[f"{var}_av"]
    if var != 'Eff':
        For_scen[var] = For_scen[var] - var_av_dict[f'{var}_av']

# Load new offline forcing data (O3t, H20s and Contrail RF calculated from fuel)
Fuel_for_RF_ltag = xr.open_dataset('/data/alecouffe/OSCAR_aviation_pv/input_data/drivers_av/fuel_scaling_factor_for_rf_av_ltag_2025_2070.nc')
df_remapped = Fuel_for_RF_ltag.assign_coords(scen=[f"{id_scen}_{s}" for s in Fuel_for_RF_ltag.scen.values])
Fuel_RF_LTAG = df_remapped.mean('sector').dropna('year', how='all')
Fuel_RF_LTAG = Fuel_RF_LTAG.interp(year=For_scen.year)   # alignement sur la grille annuelle de For_scen

## Merge For_scen and external aviation forcings
For_scen = xr.merge([For_scen, Fuel_RF_LTAG])

#--- Emissions set to 0 in NP_evt_ltag.py ---# 

For_scen = For_scen.interp(year=np.arange(2025, 2300+1))
For_scen = For_scen.transpose('year', 'reg_land', 'scen')

## specific treatment for Eluc. Does not follow O'Neill et al, 2016, but updates of extensions from the poster of Meinshausen 2019 (ScenarioForum).
For_scen['Eluc'].loc[dict(year=np.arange(2100,2150+1))] = np.linspace(For_scen['Eluc'].sel(year=2100) , 0.*For_scen['Eluc'].sel(year=2100) , 2150-2100+1)  # linear ramp over 2100-2150
For_scen['Eluc'].loc[dict(year=np.arange(2100+1,2300+1))] = 0. # 0 afterwards

## load LULCC
TMP_1 = load_landuse_scen(mod_region, ['LUH2'], LCC='gross').rename({'scen_LULCC':'scen'})

ds_TMP = TMP_1.sel(scen=id_scen)
ds_repeated_TMP = xr.concat([ds_TMP] * len(suffixes), dim='scen')
TMP = ds_repeated_TMP.assign_coords(scen=('scen', scen_names))

#TMP.coords['scen'] = [scen + '-OS' * (scen == 'SSP5-3.4') for scen in TMP['scen'].values]
TMP = TMP.where(TMP.year < 2100).dropna('year')
TMP = xr.concat([TMP, TMP.sel(year=2099).assign_coords(year=2300)], dim='year')
TMP = TMP.interp(year=np.arange(850, 2300+1))
TMP['d_Acover'] = TMP['d_Acover'].where(TMP.year <= 2099, 0)
For_scen = xr.merge([For_scen, TMP])

## load RF drivers
TMP_2 = load_RFdrivers_scen().sel(scen_RF_contr='CMIP5', scen_RF_solar='CMIP6', scen_RF_volc='CMIP6', drop=True)
TMP_2 = TMP_2.drop_vars('RF_contr')

for VAR in TMP_2:
    years = (For_hist[VAR].dropna('year').year + TMP_2[VAR].dropna('year').year).year
    For_scen[VAR] = For_hist[VAR].sel(year=years).mean('year') / TMP_2[VAR].sel(year=years).mean('year') * TMP_2[VAR]

## load atmospheric concentrations
TMP_2_load = load_data('concentrations_ScenarioMIP').drop('Xhalo_eq')
ds_TMP_2 = TMP_2_load.sel(scen=id_scen)
ds_repeated_TMP_2 = xr.concat([ds_TMP_2] * len(suffixes), dim='scen')
TMP_2 = ds_repeated_TMP_2.assign_coords(scen=('scen', scen_names))

for VAR in ['CO2', 'CH4', 'N2O', 'Xhalo']:
    For_scen['D_'+VAR] = TMP_2[VAR] - Par0[VAR+'_0']

## missing drivers
For_scen['E_Xhalo'] = 0*For_scen['D_Xhalo']

## format and save
For_scen = For_scen.sel(year=slice(2025, 2300))
For_scen = xr.concat([For_hist.sel(year=2024).drop('Aland_0'), For_scen], dim='year')
For_scen = For_scen.fillna(0)


