import json, traceback, urllib.request, urllib.parse, base64, math, time
UA = {"User-Agent": "gresmosoft-route-demo/1.0 (contact via github gresmopl)"}
pts = json.load(open("osm/track_simpl.json"))
line = ",".join(f"{a:.5f},{b:.5f}" for a, b in pts)
q = f"""[out:json][timeout:180];
way[highway](around:25,{line})->.w;
(.w;
 rel(bw.w)[route=hiking];
 nwr[amenity~"^(drinking_water|shelter|bench|toilets|restaurant|cafe|pub|fast_food|bar|parking|ice_cream|bicycle_rental|place_of_worship|fountain)$"](around:150,{line});
 nwr[natural~"^(spring|peak|saddle|cave_entrance|rock|tree|stone|cliff)$"](around:150,{line});
 nwr[tourism~"^(viewpoint|attraction|information|alpine_hut|picnic_site|artwork|museum|hotel|guest_house)$"](around:150,{line});
 nwr[historic](around:150,{line});
 nwr[man_made~"^(tower|cross|water_well)$"](around:150,{line});
 nwr[leisure~"^(picnic_table|firepit|park)$"](around:150,{line});
 nwr[shop~"^(supermarket|convenience|bakery|kiosk)$"](around:250,{line});
 node[highway=bus_stop](around:200,{line});
 nwr[railway~"^(station|halt)$"](around:500,{line});
);
out geom;"""
out = {"log": []}
def get(url, data=None, tries=3):
    for i in range(tries):
        try:
            r = urllib.request.Request(url, data=data, headers=UA)
            return urllib.request.urlopen(r, timeout=200).read()
        except Exception as e:
            body = getattr(e, "read", lambda: b"")()[:300]
            out["log"].append(f"retry {url[:80]} {e!r} {body!r}"); time.sleep(5)
    raise SystemExit("failed " + url)
out = {"log": []}
for ep in ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]:
    try:
        out["osm"] = json.loads(get(ep, urllib.parse.urlencode({"data": q}).encode())); break
    except BaseException as e: out["log"].append("osm "+ep+" "+repr(e))
print("osm", "osm" in out)
try:
    # Wikipedia geosearch every ~1.2 km
    def hav(a, b):
        la1, lo1 = map(math.radians, a); la2, lo2 = map(math.radians, b)
        h = math.sin((la2-la1)/2)**2 + math.cos(la1)*math.cos(la2)*math.sin((lo2-lo1)/2)**2
        return 2*6371000*math.asin(math.sqrt(h))
    probe = [pts[0]]
    for p in pts:
        if hav(probe[-1], p) > 1200: probe.append(p)
    pages = {}
    for lang in ["pl"]:
        for a, b in probe:
            u = f"https://{lang}.wikipedia.org/w/api.php?action=query&list=geosearch&gscoord={a}|{b}&gsradius=700&gslimit=30&format=json"
            for g in json.loads(get(u))["query"]["geosearch"]:
                pages[g["pageid"]] = g
            time.sleep(0.3)
    print("wiki pages", len(pages))
    ids = list(pages)
    det = {}
    for i in range(0, len(ids), 20):
        u = ("https://pl.wikipedia.org/w/api.php?action=query&prop=extracts|pageimages|info&inprop=url&exintro=1&explaintext=1&exsentences=3"
             "&piprop=thumbnail&pithumbsize=480&format=json&pageids=" + "|".join(map(str, ids[i:i+20])))
        det.update(json.loads(get(u))["query"]["pages"])
    wiki = []
    for pid, g in pages.items():
        d = det.get(str(pid), {})
        item = {"id": pid, "title": g["title"], "lat": g["lat"], "lon": g["lon"], "extract": d.get("extract", ""), "url": d.get("fullurl")}
        th = d.get("thumbnail", {}).get("source")
        if th:
            try:
                item["img"] = "data:image/jpeg;base64," + base64.b64encode(get(th)).decode()
            except SystemExit: pass
        wiki.append(item)
    out["wiki"] = wiki
except BaseException:
    out["log"].append(traceback.format_exc())
json.dump(out, open("osm/route_data.json", "w"), ensure_ascii=False)
