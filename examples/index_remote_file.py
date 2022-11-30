"""
Example using a series of small byte range requests to inventory a remote GRIB2 file on NOMADS
"""
from datetime import datetime, timedelta

from beltzer import Index
from beltzer.downloaders import http_download
from beltzer.grib2 import Grib2

model_run = (datetime.utcnow() - timedelta(days=1)).strftime('%Y%m%d')
grib_url = f'https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.{model_run}/12/atmos/gfs.t12z.pgrb2.0p25.f001'
grib2 = Grib2.open_remote(grib_url, http_download)
index = Index.from_grib2(grib2)
index.to_ncep_idx('remote.idx')
