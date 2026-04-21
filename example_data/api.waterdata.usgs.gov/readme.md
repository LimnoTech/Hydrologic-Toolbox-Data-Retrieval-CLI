# New api

Landing: https://api.waterdata.usgs.gov/ogcapi/v0/

JSON
- Monitoring Locations: https://api.waterdata.usgs.gov/ogcapi/v0/collections/monitoring-locations/items?f=json&lang=en-US&limit=10&skipGeometry=false&offset=0&id=USGS-02225500
- Daily values: https://api.waterdata.usgs.gov/ogcapi/v0/collections/daily/items?f=json&lang=en-US&limit=50000&properties=time,value,unit_of_measure&skipGeometry=true&sortby=time&offset=0&datetime=1900-01-01%2F2100-01-01&monitoring_location_id=USGS-02225500&parameter_code=00060 


CSV
- https://api.waterdata.usgs.gov/ogcapi/v0/collections/monitoring-locations/items?f=csv&lang=en-US&limit=10&skipGeometry=false&offset=0&id=USGS-02225500
- https://api.waterdata.usgs.gov/ogcapi/v0/collections/daily/items?f=csv&lang=en-US&limit=50000&properties=time,value,unit_of_measure&skipGeometry=true&sortby=time&offset=0&datetime=1900-01-01%2F2100-01-01&monitoring_location_id=USGS-02225500&parameter_code=00060

JSONLD
HTML