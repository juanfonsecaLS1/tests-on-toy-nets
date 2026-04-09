# loading packages
pkgs <- c("sf","osmextract","tidyverse")
pak::pkg_install(
  pkgs,
  ask = FALSE
)
sapply(pkgs, require, character.only = TRUE)

# Creating a directory for saving the data
dir.create("raw_nets_gpkg", showWarnings = FALSE)


# Creating a tibble with the coordinates of the cities we want
cities <- tribble(
  ~city_name, ~lat, ~lon,
    "Lima",  -12.077948042115647,  -77.05096688507561,
    "Brussels",  50.856117793777145,  4.381718424984715,
    "Rome",  41.89900799198937,  12.512797548177907,
    "Cairo",  30.036716997454857,  31.23947439245143,
    "Salt Lake City",  40.75984495218752,  -111.88769690322184,
    "Bogota",  4.646242884611647,  -74.08436455625211,
    "Leeds",  53.81303429075668,   -1.508881353201933,
    "Milton Keynes",  52.0367171540023,  -0.7324001661371712,
    "Lisbon",  38.72778849555562,  -9.162267565552924,
    "New York",  40.7589664816669,  -73.96121069380527,
    "Brasilia",  -15.76133509896713,  -47.88377302616466,
    "Sao Paulo",  -23.54468352821393,  -46.67047368527096
)

# We are interested in a 10 km buffer around the coordinates
buffer_size <- 10e3

# Transforming the coordinates into spatial objects and producing a buffer around them
cities_sf <- st_as_sf(cities, coords = c("lon", "lat"), crs = 4326) |> 
  st_buffer(buffer_size)

# A loop to extract the driving network and saving the extract as a GeoPackage for further processing
lapply(cities_sf$city_name, 
  function(city){
  oe_get_network(cities_sf$geometry[cities_sf$city_name == city],
     mode = "driving", extra_tags = "maxspeed",
     boundary = cities_sf$geometry[cities_sf$city_name == city]) |> 
      st_write(file.path("raw_nets_gpkg",paste(city,"gpkg",sep = ".")),append = FALSE)
})


  
oe_get