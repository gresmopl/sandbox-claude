import json, traceback, urllib.request, urllib.parse, base64, math, time

UA = {"User-Agent": "gresmosoft-route-demo/1.0 (github.com/gresmopl)"}
out = {"log": []}
pts = json.load(open("osm/track_simpl.json"))
line = ",".join(f"{a:.5f},{b:.5f}" for a, b in pts)


def get(url, data=None, tries=6):
    for i in range(tries):
        try:
            r = urllib.request.Request(url, data=data, headers=UA)
            return urllib.request.urlopen(r, timeout=200).read()
        except Exception as e:
            out["log"].append(f"retry {url[:80]} {e!r}")
            time.sleep(10 * (i + 1))
    raise RuntimeError("failed " + url[:80])


def hav(a, b):
    la1, lo1 = map(math.radians, a); la2, lo2 = map(math.radians, b)
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * 6371000 * math.asin(math.sqrt(h))


q = f"""[out:json][timeout:180];
way[highway](around:25,{line})->.w;
rel(bw.w)[route=hiking]->.r;
(
 .w; .r;
 nwr[amenity~"^(drinking_water|shelter|bench|toilets|restaurant|cafe|pub|fast_food|bar|parking|ice_cream|place_of_worship|fountain)$"](around:150,{line});
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

try:
    for ep in ["https://overpass.kumi.systems/api/interpreter", "https://overpass-api.de/api/interpreter",
               "https://overpass.private.coffee/api/interpreter"]:
        try:
            r = json.loads(get(ep, urllib.parse.urlencode({"data": q}).encode()))
            out["log"].append(f"{ep} elements={len(r.get('elements', []))} remark={r.get('remark')}")
            if r.get("elements"):
                out["osm"] = r
                break
        except Exception as e:
            out["log"].append(f"osm {ep} {e!r}")
except Exception:
    out["log"].append(traceback.format_exc())

try:
    probe = [pts[0]]
    for p in pts:
        if hav(probe[-1], p) > 1200:
            probe.append(p)
    pages = {}
    for a, b in probe:
        u = "https://pl.wikipedia.org/w/api.php?" + urllib.parse.urlencode(
            {"action": "query", "list": "geosearch", "gscoord": f"{a}|{b}", "gsradius": 700, "gslimit": 30, "format": "json"})
        resp = json.loads(get(u))
        if "query" not in resp:
            out["log"].append("wiki " + str(resp)[:200]); continue
        for g in resp["query"]["geosearch"]:
            pages[g["pageid"]] = g
        time.sleep(0.5)
    ids = list(pages); det = {}
    for i in range(0, len(ids), 20):
        u = "https://pl.wikipedia.org/w/api.php?" + urllib.parse.urlencode({
            "action": "query", "prop": "extracts|pageimages|info", "inprop": "url", "exintro": 1, "explaintext": 1,
            "exsentences": 3, "piprop": "thumbnail", "pithumbsize": 480, "format": "json",
            "pageids": "|".join(map(str, ids[i:i + 20]))})
        det.update(json.loads(get(u)).get("query", {}).get("pages", {}))
    wiki = []
    for pid, g in pages.items():
        d = det.get(str(pid), {})
        item = {"id": pid, "title": g["title"], "lat": g["lat"], "lon": g["lon"],
                "extract": d.get("extract", ""), "url": d.get("fullurl")}
        th = d.get("thumbnail", {}).get("source")
        if th:
            try:
                item["img"] = "data:image/jpeg;base64," + base64.b64encode(get(th, tries=2)).decode()
            except Exception as e:
                out["log"].append(f"img {e!r}")
        wiki.append(item)
    out["wiki"] = wiki
except Exception:
    out["log"].append(traceback.format_exc())

json.dump(out, open("osm/route_data.json", "w"), ensure_ascii=False)
print("\n".join(out["log"][-10:]))
