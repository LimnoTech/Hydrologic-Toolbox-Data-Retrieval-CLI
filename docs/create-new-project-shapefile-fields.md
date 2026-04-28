# Create New Project Shapefile Fields

## Kept Fields

The shapefile exports produced by `create-new-project` keep this reduced field set:

- `site_no`
- `loc_id`
- `stn_name`
- `site_tp`
- `state_cd`
- `county_cd`
- `lat`
- `lon`
- `agency_cd`
- `huc_code`

## Why the Schema Was Reduced

- Shapefiles have a 10-character field-name limit, so long raw Water Data column names do not survive cleanly.
- Several raw fields are duplicates or near-duplicates of the values we already keep.
- Many of the dropped fields are useful for archival detail but make the station shapefiles harder to read in GIS tools.
- The reduced schema keeps the fields most useful for mapping, station identification, and quick filtering.

## Excluded Columns

Excluded columns include the remaining raw station-discovery fields, especially:

- descriptive duplicates such as `agency_name`, `monitoring_location_number`, `monitoring_location_name`, `site_type`, `state_name`, `county_name`, and `country_name`
- raw aliases already represented by kept columns such as `state_code`, `county_code`, `site_type_code`, `dec_lat_va`, `dec_long_va`, `station_nm`, and `monitoring_location_id`
- coordinate-reference, accuracy, and revision metadata such as `altitude`, `vertical_datum`, `horizontal_positional_accuracy`, `revision_created`, and `revision_modified`
- workflow/helper columns such as `workflow_type`, `geometry_type`, and the expanded CSV-style `geometry` payload
- groundwater construction and aquifer metadata such as `construction_date`, `aquifer_code`, `national_aquifer_code`, `well_constructed_depth`, and `hole_constructed_depth`

## Result

The exported shapefiles stay easier to open, easier to interpret, and more stable across GIS tools while still carrying the key fields needed for the create-project workflow.
