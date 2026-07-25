#!/usr/bin/env python3
"""Reverse geocode GPS coordinates using OpenStreetMap Nominatim."""
import sys, json, time, urllib.request

def reverse_geocode(lat, lon):
    url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json&zoom=18&addressdetails=1"
    req = urllib.request.Request(url, headers={'User-Agent': 'PhotoGeolocator/1.0'})
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read())
        addr = data.get('address', {})
        return {
            "lat": lat, "lon": lon,
            "name": data.get('name', ''),
            "house_number": addr.get('house_number', ''),
            "road": addr.get('road', ''),
            "neighbourhood": addr.get('neighbourhood', addr.get('suburb', '')),
            "city": addr.get('city', addr.get('town', addr.get('village', ''))),
            "state": addr.get('state', ''),
            "country": addr.get('country', ''),
            "postcode": addr.get('postcode', ''),
            "amenity": addr.get('amenity', addr.get('shop', addr.get('leisure', ''))),
            "display_name": data.get('display_name', '')
        }
    except Exception as e:
        return {"lat": lat, "lon": lon, "error": str(e)}

def main():
    if len(sys.argv) == 2:
        # JSON file input: [{"lat": x, "lon": y}, ...]
        with open(sys.argv[1]) as f:
            coords = json.load(f)
        results = []
        for c in coords:
            if c.get('lat') and c.get('lon'):
                results.append(reverse_geocode(c['lat'], c['lon']))
                time.sleep(1.1)  # respect Nominatim rate limit
            else:
                results.append({"lat": c.get('lat'), "lon": c.get('lon'), "error": "missing coordinates"})
        print(json.dumps(results, indent=2))
    elif len(sys.argv) == 3:
        # Direct lat lon input
        result = reverse_geocode(float(sys.argv[1]), float(sys.argv[2]))
        print(json.dumps(result, indent=2))
    else:
        print("Usage: reverse_geocode.py <lat> <lon>  OR  reverse_geocode.py <coords.json>", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
