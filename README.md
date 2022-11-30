# Beltzer

Belzer allows you to retrieve specific messages from remote GRIB files, even when there's no index file available.

## Background
Often GRIB files are accompanied by index files which indicate the position of the first byte of each message within the GRIB file. Using this information you can then download just the bytes of the fields you need rather than the entire message. Unfortunately these index files are sometimes missing and you can't directly use the index file from a different file in the same as the byte offsets almost always differ.
Beltzer tackles this problem by intelligently parsing the GRIB file to reconstruct missing index files or using index files from other files in the same product to make educated guesses to identify the bytes in the target file, all without needing to download the entire file.

## Example
```
"""
Inventory a recent remote GFS GRIB2 file on NOMADS without downloading the entire file
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
```
