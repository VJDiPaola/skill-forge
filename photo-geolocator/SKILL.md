---
name: photo-geolocator
description: Extract when and where photos were taken using EXIF metadata, then reverse geocode GPS coordinates to venues, restaurants, and addresses. Trigger on "where was this taken," uploaded photos with where/when questions, mapping photos to places, converting GPS coordinates to addresses, or any mention of photo metadata, geolocation, or geotagging. Also the reusable building block when another skill needs date/location from photos.
---

# Photo Geolocator

Extract date, time, and GPS location from photos via EXIF metadata, then reverse geocode coordinates to street addresses and venue names using OpenStreetMap Nominatim.

## When to use this skill

- User uploads photos and asks "where was this taken?" or "when was this?"
- Any workflow that needs to go from photo files → dates and locations
- Another skill (like the wine journal) needs date/location extraction as a building block
- User wants to map a set of photos to venues, restaurants, cities, or trips

## How it works

### Step 1: Extract EXIF data

Run the bundled extraction script on the photo directory or individual files:

```bash
pip install Pillow --break-system-packages -q
python3 <skill-path>/scripts/extract_exif.py <directory_or_file>
```

This outputs JSON with `file`, `date`, `lat`, `lon` for each image. Dates are in `YYYY:MM:DD HH:MM:SS` format. GPS coordinates are decimal degrees (positive = N/E, negative = S/W).

Not all photos have EXIF data — phone cameras almost always do, but screenshots, downloaded images, and some edited photos won't. When GPS is missing, note it as "Unknown location" rather than guessing.

### Step 2: Cluster nearby coordinates

Photos taken at the same venue will have slightly different GPS readings (within ~50m). Before reverse geocoding, cluster coordinates that are within 0.001° of each other (roughly 100m) to avoid redundant API calls.

```python
# Cluster logic: group points within 0.001° lat AND 0.001° lon
clusters = {}
for point in exif_results:
    if point['lat'] is None:
        continue
    matched = False
    for key in clusters:
        if abs(point['lat'] - key[0]) < 0.001 and abs(point['lon'] - key[1]) < 0.001:
            clusters[key].append(point)
            matched = True
            break
    if not matched:
        clusters[(point['lat'], point['lon'])] = [point]
```

### Step 3: Reverse geocode

Run the bundled reverse geocoding script on the unique coordinate clusters:

```bash
python3 <skill-path>/scripts/reverse_geocode.py <coords.json>
```

Where `coords.json` is a JSON array of `{"lat": x, "lon": y}` objects. The script respects Nominatim's 1-request-per-second rate limit automatically.

The output includes `name` (venue name if OSM knows it), `road`, `house_number`, `neighbourhood`, `city`, `country`, and `amenity`.

### Step 4: Identify specific venues

Nominatim gives you the street address, but often not the specific restaurant or bar. To identify the actual venue:

1. Check the `name` and `amenity` fields first — sometimes Nominatim returns the venue directly (e.g., "Andrew Edmunds", "Le Dive")
2. For addresses without a venue name, use WebSearch to search for restaurants/bars at that specific address: `restaurant "123 Main Street" [city]`
3. If the photo itself shows a venue name (menu, signage, receipt), that's the most reliable identification
4. For coordinates in residential areas visited repeatedly across many dates, these are likely the user's home — flag as "Home ([neighborhood])" rather than searching for restaurants
5. For coordinates on park drives or waterfront walkways, these are likely outdoor picnics — flag as "[Park name] (picnic)" or "Waterfront (outdoor)"

### Step 5: Present results

Return a structured summary with: date (reformatted to YYYY-MM-DD), city/neighborhood, specific venue (if identified), and the street address as fallback.

## Tips for accuracy

- **Recurring locations**: If the same GPS cluster appears across many different dates (5+ visits), it's almost certainly the user's home or office, not a restaurant.
- **Same-day clusters**: Multiple photos at the same coordinates on the same day are the same venue visit. Group them.
- **Sequential photos**: Photos taken minutes apart at the same coordinates are the same event (e.g., front and back of a wine label, multiple dishes at dinner).
- **Travel patterns**: Look at the dates and cities holistically to understand trips. E.g., Dublin → London on consecutive days = a Europe trip.

## Dependencies

- Python 3 with Pillow (`pip install Pillow --break-system-packages`)
- Internet access for Nominatim reverse geocoding and WebSearch for venue identification
