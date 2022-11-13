from beltzer import Index, grib2, find_remote_message
from beltzer.downloaders import http_download

grib = grib2.Grib2.open_grib('/home/joxtoby/blog/grib/gfs.t06z.pgrb2.0p25.f026')
index = Index.from_grib2(grib)
entry = index.get_entry(parameter='TMP', level='ground or water surface')
grib_url = 'https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.20221124/06/atmos/gfs.t06z.pgrb2.0p25.f010'
message = find_remote_message(grib_url, index, entry.message_number, http_download)
if message:
    with open('surface_temp.grib2', 'wb') as f:
        f.write(message.raw_bytes)

