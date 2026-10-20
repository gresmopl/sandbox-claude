[out:json][timeout:180][bbox:50.580,16.130,50.772,16.430];
area["ISO3166-1"="PL"]->.p;
rel[route=hiking]->.r;
(
  nwr[amenity=parking](area.p);
  node[highway=trailhead];
  node[natural=peak];
  node[natural=saddle];
  nwr[tourism~"alpine_hut|wilderness_hut|viewpoint|hotel|guest_house"](area.p);
  way[highway~"^(primary|secondary|tertiary|unclassified|residential)$"];
  way(r.r);
  way[admin_level=2];
  way[landuse=forest];
  way[natural=wood];
  node[place~"village|town|hamlet"];
);
out geom;
.r out body;
