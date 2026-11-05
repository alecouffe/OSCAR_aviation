
'''
RUN OSCAR-Aviation - Version 3.3 - @author: alecouffe
'''

import xarray as xr

## being  in the OSCAR folder, import the model
from core_fct.mod_process_av import OSCAR

'''
## load primary parameters
## note: requires choosing a 'mod_region' 
from core_fct.fct_loadP_av import load_all_param
Par0 = load_all_param(mod_region='RCP_5reg')

## generate Monte Carlo set of parameters
## note: requires choosing 'nMC' (here, 200 elements)
from core_fct.fct_genMC import generate_config
Par = generate_config(Par0, nMC=400)
'''

Par = xr.open_dataset('/OSCAR_aviation/results/Par_example.nc')

new_vars = ['tau_CH4', 'RF_atm', 'RF_warm', 'RF_slcf', 'f_kOH', 'RF_O3t', 'D_O3t', 'D_NO3', 'RF', 'D_SO4', 'D_SO4_av', 'RF_SO4_av', 'D_POA', 'D_POA_av', 'RF_POA', 'RF_POA_av', 'D_BC', 'D_BC_av', 'RF_BC_av', 'D_Eluc', 'D_Focean', 'D_Fland', 'D_Epf'] + ['tau_CH4', 'tau_N2O'] + [var for var in list(OSCAR._processes.keys()) if 'RF' in var]


##----------------------------------------------------------------------------------------------------
# NOTES : 
# Remove 'D_CO2', 'D_CH4', 'D_N2O' from For_ (it erase the MC configuration of the previous variable)
# Then move parameters from For to Par (some parameters may come from driving datasets (normally, Aland_0)) 
# For scenarios, take Ini from last year of For_hist
# Run the model and save
##---------------------------------------------------------------------------------------------------

# NOTES : HISTORICAL PLANE

from run_scripts.P_evt_ssp import For_hist

del_var = ['D_CO2', 'D_CH4', 'D_N2O']
for var_name in del_var:
    if var_name in For_hist:
        del For_hist[var_name]

Par = xr.merge([Par, For_hist.drop([VAR for VAR in For_hist if 'year' in For_hist[VAR].dims])])
For_hist = For_hist.drop([VAR for VAR in For_hist if 'year' not in For_hist[VAR].dims])

Out_hist_plane = OSCAR(Ini=None, Par=Par, For=For_hist, var_keep=new_vars, nt=6)
Out_hist_plane.to_netcdf('/OSCAR_aviation/results/Out_hist_plane.nc')

##--------------------
## NOTES : SSP PLANE

#Out_hist_plane = xr.open_dataset('/OSCAR_aviation/results/Out_hist_plane.nc')

from run_scripts.P_evt_ssp import For_scen
For_scen = For_scen.sel(year=slice(None, 2100))

del_var = ['D_CO2', 'D_CH4', 'D_N2O']
for var_name in del_var:
    if var_name in For_scen:
        del For_scen[var_name]

Ini = Out_hist_plane.isel(year=-1, drop=True)

Out_scen_plane = OSCAR(Ini=Ini, Par=Par, For=For_scen, var_keep=new_vars, nt=10)
Out_scen_plane.to_netcdf('/OSCAR_aviationi/results/Out_scen_plane.nc')

##----------------------------------------------------------------------------------------------------------
## NOTES :  NOPLANE

from run_scripts.NP_evt_ssp import build_ssp_drivers

def sp_tag(SP_list):
    #Tag from SP_list.
    #Ex: 'E_NOX_av' -> 'NOX', 'factor_RF_Contr' -> 'Contr', 'Eff_av' -> 'CO2' 
    if not SP_list:
        return 'ref'

    SPECIAL_CASES = {'Eff_av': 'CO2'}  # particular case
    SUFFIXES = ['_av']
    PREFIXES = ['factor_RF_', 'fuel_RF_', 'E_', 'RF_', 'D_'] 

    parts = []
    for sp in SP_list:
        if sp in SPECIAL_CASES:
            parts.append(SPECIAL_CASES[sp])
            continue
        name = sp
        for suf in SUFFIXES:
            if name.endswith(suf):
                name = name[:-len(suf)]
                break
        for pre in PREFIXES:
            if name.startswith(pre):
                name = name[len(pre):]
                break
        parts.append(name)
    return '_'.join(parts)

# Specie(s) to 0 here : effective in NP_evt_ssp.py
SP_list = ['E_SO2_av']
# "Eff_av" "factor_RF_H2Os_av" "E_BC_av" "E_SO2_av" "E_OC_av" "factor_RF_contr" "factor_RF_O3t_av" "E_NOX_av"

For_hist, For_scen_np = build_ssp_drivers(SP_list=SP_list)

TAG = sp_tag(SP_list)

##--------------------
## NOTES : HISTORICAL NOPLANE

del_var = ['D_CO2', 'D_CH4', 'D_N2O']
for var_name in del_var:
    if var_name in For_hist:
        del For_hist[var_name]

Par = xr.merge([Par, For_hist.drop([VAR for VAR in For_hist if 'year' in For_hist[VAR].dims])])
For_hist = For_hist.drop([VAR for VAR in For_hist if 'year' not in For_hist[VAR].dims])

Out_hist_noplane = OSCAR(Ini=None, Par=Par, For=For_hist, var_keep=new_vars, nt=6)
Out_hist_noplane.to_netcdf(f'/OSCAR_aviation/results/Out_hist_noplane_{TAG}.nc')

##--------------------
## NOTES : SSP NO PLANE

#Out_hist_noplane = xr.open_dataset('/OSCAR_aviation/results/Out_hist_noplane_{TAG}.nc')
## -> If you use this line instead of the “Historical NOPLANE” block above,
##    For_scen_np remains available because build_ssp_drivers() was called separately earlier

For_scen = For_scen_np.sel(year=slice(None, 2100))

del_var = ['D_CO2', 'D_CH4', 'D_N2O']
for var_name in del_var:
    if var_name in For_scen:
        del For_scen[var_name]

Ini = Out_hist_noplane.isel(year=-1, drop=True)

Out_scen_noplane = OSCAR(Ini=Ini, Par=Par, For=For_scen, var_keep=new_vars, nt=10)
Out_scen_noplane.to_netcdf(f'/OSCAR_aviation/results/Out_scen_noplane_{TAG}.nc')

##--------------------


