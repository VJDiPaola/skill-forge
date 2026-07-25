#!/usr/bin/env python3
"""Extract EXIF date and GPS coordinates from image files."""
import os, sys, json
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

def dms_to_dd(dms, ref):
    d, m, s = [float(x) for x in dms]
    dd = d + m/60 + s/3600
    if ref in ('S', 'W'):
        dd *= -1
    return round(dd, 6)

def extract_exif(path):
    try:
        img = Image.open(path)
        exif_data = img._getexif()
        if not exif_data:
            return {"file": os.path.basename(path), "date": None, "lat": None, "lon": None}
        result = {}
        gps_info = {}
        for tag_id, value in exif_data.items():
            tag = TAGS.get(tag_id, tag_id)
            if tag == 'GPSInfo':
                for k, v in value.items():
                    gps_info[GPSTAGS.get(k, k)] = v
            elif tag in ('DateTimeOriginal', 'DateTime', 'DateTimeDigitized'):
                if tag not in result or tag == 'DateTimeOriginal':
                    result[tag] = str(value)
        date_str = result.get('DateTimeOriginal', result.get('DateTime', result.get('DateTimeDigitized')))
        lat = lon = None
        if 'GPSLatitude' in gps_info and 'GPSLongitude' in gps_info:
            lat = dms_to_dd(gps_info['GPSLatitude'], gps_info.get('GPSLatitudeRef', 'N'))
            lon = dms_to_dd(gps_info['GPSLongitude'], gps_info.get('GPSLongitudeRef', 'W'))
        return {"file": os.path.basename(path), "date": date_str, "lat": lat, "lon": lon}
    except Exception as e:
        return {"file": os.path.basename(path), "date": None, "lat": None, "lon": None, "error": str(e)}

def main():
    if len(sys.argv) < 2:
        print("Usage: extract_exif.py <directory_or_file> [...]", file=sys.stderr)
        sys.exit(1)
    results = []
    for arg in sys.argv[1:]:
        if os.path.isdir(arg):
            for f in sorted(os.listdir(arg)):
                if f.lower().endswith(('.jpg', '.jpeg', '.png', '.heic', '.tiff')):
                    results.append(extract_exif(os.path.join(arg, f)))
        elif os.path.isfile(arg):
            results.append(extract_exif(arg))
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
