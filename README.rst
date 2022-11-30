# Beltzer

Belzer allows you to retrieve specific messages from remote GRIB files, even when there's no index file available.

## Background
Often GRIB files are accompanied by index files which indicate the position of the first byte of each message within the GRIB file. Using this information you can then download just the bytes of the fields you need rather than the entire message. Unfortunately these index files are sometimes missing and you can't directly use the index file from a different file in the same as the byte offsets almost always differ.
Beltzer tackles this problem by intelligently parsing the GRIB file to reconstruct missing index files or using index files from other files in the same product to make educated guesses to identify the bytes in the target file, all without needing to download the entire file.

## Example
```

