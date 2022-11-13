"""
Download and index yesterday's 12Z GFS atmos f001 file from NOMADS.
"""
from datetime import datetime, timedelta
from beltzer import Index
from beltzer.downloaders import http_download
from beltzer.grib2 import Grib2


model_run = (datetime.utcnow() - timedelta(days=1)).strftime('%Y%m%d')
grib_url = f'https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.{model_run}/12/atmos/gfs.t12z.pgrb2.0p25.f001'
#grib_bytes = http_download(grib_url)
#with open('tmp.grb', 'wb') as f:
#    f.write(grib_bytes)
with open('tmp.grb', 'rb') as f:
    grib_bytes = f.read()
grib2 = Grib2.open_grib(grib_bytes)
index = Index.from_grib2(grib2)
index.to_ncep_idx('gfs.t12z.pgrb2.0p25.f001.idx')
