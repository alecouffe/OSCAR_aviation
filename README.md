# OSCAR-Aviation
Lecouffe, A., D. Hauglustaine, N. Bellouin, and T. Gasser: The climate impact of aviation simulated with the OSCAR-Aviation reduced complexity model, in preparation.

# How to use
First, download OSCAR v3.3, the version on which OSCAR-Aviation is built (https://github.com/tgasser/OSCAR/tree/v3.3), for example with:

```
git clone --branch v3.3 https://github.com/tgasser/OSCAR
```

OSCAR is described in: Gasser, T., P. Ciais, O. Boucher, Y. Quilcaille, M. Tortora, L. Bopp, and D. Hauglustaine: The compact Earth system model OSCAR v2.2: description and first results, Geosci. Model Dev., 10, 271–319, https://doi.org/10.5194/gmd-10-271-2017, 2017.

Then, merge the files in each folder with the same name **from OSCAR-Aviation to OSCAR**.  
For example, in `core_fct`, copy `fct_loadP_av.py` from OSCAR-Aviation to OSCAR.  
In `input_data`, copy `drivers_av` from OSCAR-Aviation to OSCAR. Etc.  

Most files are new: they are added to OSCAR, and the scripts use them instead of the original OSCAR files (e.g., `mod_process_av.py` instead of `mod_process.py`).  
One file replaces the OSCAR file of the same name: `input_data/parameters/from_OSCARv2/aerchem_ACCMIP.nc`, in which some lifetimes were modified (the modifications are dated in the file metadata, visible with `ncdump -h`).

## Requirements
OSCAR-Aviation was developed and run with Python 3.8.8 and the following packages: `numpy` (v1.20.1), `scipy` (v1.6.2), `xarray` (v0.18.0), `netCDF4` (v1.5.3) and `pandas` (v1.2.4).

## Running time of simulations
On the IPSL computing server, with 400 Monte-Carlo members:
- 30 minutes for the historical part (nt = 6)
- 21 minutes for the scenarios part (~12 scenarios, nt = 10)

nt is the number of sub-time steps per year (the time step is 1/nt year).

## Simulations
To perform a simulation for SSP or LTAG scenarios, run the `script_oscar_VAR_scen.py` script, which calls the model and the plane and noplane functions that read the emissions.  
By default, the LTAG scenarios are run with SSP3-7.0 as the background scenario for the non-aviation sectors, but users can choose any other scenario.  
The set of parameters and the Monte-Carlo draw must be the same for simulations to be compared, so be careful to save the `Par` variable at the end of the first simulation (an example with 20 Monte-Carlo members is provided as `Par_example.nc`).

## Scripts
### Functions in run_scripts/

- `(N)P_evt_ltag.py` for LTAG scenarios
- `(N)P_evt_ssp.py` for SSP scenarios

These plane (P) and noplane (NP)[^2] functions are one example of how OSCAR-Aviation can be used: users can adapt them or write their own.

### Core of the model in core_fct/

- `mod_process_av.py`: equations[^1]
- `fct_loadP_av.py`: parameters

## Inputs
### In input_data/drivers_av/

- `emission_hist_1750_2024.nc`: historical emissions, all sectors
- `emission_ssp_2025_2100.nc`: SSP scenarios (after the new handshake[^3]), all sectors
- `emission_ltag_av_2025_2070.nc`: global emissions from LTAG scenarios (aviation sector for CO2, BC, SO2 and NOx)

- `fuel_scaling_factor_for_rf_av_hist_1750_2024.nc`: fuel scaling factor for the O3t, H2Os and contrails RF calculations
- `fuel_scaling_factor_for_rf_av_ssp_2025_2100.nc`: same for SSP
- `fuel_scaling_factor_for_rf_av_ltag_2025_2070.nc`: same for LTAG

# License
OSCAR-Aviation is distributed under the CeCILL 2.1 license, like OSCAR (see `LICENSE`).

# Contact
Audrey Lecouffe: alecouffe@ipsl.fr

[^1]: RF variables are ERF.

[^2]: In the noplane functions (`NP_evt_ltag.py` and `NP_evt_ssp.py`), define the species to set to 0 at the beginning of the code with `SP_list`.

[^3]: Historical emissions are from different inventories. Emissions from the Community Emissions Data System (CEDS) project are used over the period 1750–2022. The Coupled Model Intercomparison Project (CMIP6) inventory from 1750 to 2014, and the Global Fire Emissions Database (GFED4) from 2015 to 2022, are added for the biomass burning sectors. Shared Socio-economic Pathways (SSP) scenarios are available from 2015 to 2100, with emission values provided at decadal intervals. For optimal continuity between the historical and scenario periods, the 2015–2024 period of the SSP scenarios was excluded from the data, as it is outdated. Instead, emissions in 2024 are set equal to those of 2019, since emissions in 2024 returned to 2019 levels (Dannet et al., 2024; Lecouffe et al., in prep.), and emissions in 2023 are interpolated between 2022 and 2024. Then, a sectoral mapping and a new "handshake" procedure were implemented between 2024 (end of the historical period) and 2030 (beginning of the scenarios).
