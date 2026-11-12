#!/usr/bin/env python3
"""Extrait les horaires théoriques RER, Transilien et tram-trains du GTFS IDFM.
Usage : python3 extraire-horaires.py <dossier-gtfs ou fichier .zip> [nombre_de_jours] [dossier_de_sortie]
Produit horaires-ferres.json et horaires-ferres.json.gz dans le dossier de sortie (dossier courant par défaut).
Source : Île-de-France Mobilités, offre horaires TC GTFS (licence ODbL).
"""
import csv, json, os, sys, datetime as dt, re, io, zipfile, gzip

if len(sys.argv) < 2:
    sys.exit("Indique le dossier GTFS décompressé, par exemple : python3 extraire-horaires.py ~/Downloads/IDFM_gtfs")
G = os.path.expanduser(sys.argv[1])
NDAYS = int(sys.argv[2]) if len(sys.argv) > 2 else 7
OUT = os.path.expanduser(sys.argv[3]) if len(sys.argv) > 3 else "."
ZIP = zipfile.ZipFile(G) if G.lower().endswith(".zip") else None
TRAMTRAIN = {"T4", "T11", "T12", "T13"}

def rd(name):
    if ZIP:
        m = [n for n in ZIP.namelist() if n.split("/")[-1] == name]
        if not m:
            return None
        return csv.DictReader(io.TextIOWrapper(ZIP.open(m[0]), encoding="utf-8-sig", newline=""))
    p = os.path.join(G, name)
    if not os.path.exists(p):
        return None
    return csv.DictReader(open(p, encoding="utf-8-sig", newline=""))

print("1/5 Lignes…")
routes = {}
for r in rd("routes.txt"):
    if r["route_type"] == "2" or (r["route_type"] == "0" and r["route_short_name"] in TRAMTRAIN):
        if "emplacement" in r.get("route_long_name", ""):
            continue
        routes[r["route_id"]] = r["route_short_name"]

print("2/5 Calendriers…")
today = dt.date.today()
dates = [today + dt.timedelta(days=i) for i in range(NDAYS)]
active = {d.isoformat(): set() for d in dates}
cal = rd("calendar.txt")
if cal:
    for c in cal:
        a = dt.datetime.strptime(c["start_date"], "%Y%m%d").date()
        b = dt.datetime.strptime(c["end_date"], "%Y%m%d").date()
        wd = [c["monday"], c["tuesday"], c["wednesday"], c["thursday"], c["friday"], c["saturday"], c["sunday"]]
        for d in dates:
            if a <= d <= b and wd[d.weekday()] == "1":
                active[d.isoformat()].add(c["service_id"])
cd = rd("calendar_dates.txt")
if cd:
    for c in cd:
        d = dt.datetime.strptime(c["date"], "%Y%m%d").date().isoformat()
        if d in active:
            if c["exception_type"] == "1":
                active[d].add(c["service_id"])
            else:
                active[d].discard(c["service_id"])
used_services = set().union(*active.values())

print("3/5 Courses…")
trips = {}
for t in rd("trips.txt"):
    if t["route_id"] in routes and t["service_id"] in used_services:
        trips[t["trip_id"]] = [routes[t["route_id"]], t["trip_headsign"], t["trip_short_name"], t["service_id"]]

print("4/5 Arrêts…")
stops = {}
for s in rd("stops.txt"):
    stops[s["stop_id"]] = s
def zone(sid):
    s = stops.get(sid, {})
    par = s.get("parent_station") or sid
    m = re.search(r"(\d+)\D*$", par)
    return m.group(1) if m else par
def sname(sid):
    s = stops.get(sid, {})
    par = s.get("parent_station")
    return (stops.get(par, {}).get("stop_name") if par else None) or s.get("stop_name", "")

print("5/5 Horaires (le plus long, plusieurs minutes)…")
calls = {}
n = 0
for st in rd("stop_times.txt"):
    n += 1
    if n % 2000000 == 0:
        print("   ", n, "lignes lues…")
    tid = st["trip_id"]
    if tid not in trips:
        continue
    tm = st["departure_time"] or st["arrival_time"]
    if not tm:
        continue
    h, m, _ = tm.split(":")
    calls.setdefault(tid, []).append((int(st["stop_sequence"]), st["stop_id"], int(h) * 60 + int(m),
                                      st.get("pickup_type", "0"), st.get("drop_off_type", "0")))

zidx, znames, svc_idx = {}, [], {}
def zi(sid):
    z = zone(sid)
    if z not in zidx:
        zidx[z] = len(znames)
        znames.append([z, sname(sid)])
    return zidx[z]
def si(s):
    if s not in svc_idx:
        svc_idx[s] = len(svc_idx)
    return svc_idx[s]

out_trips = []
for tid, cl in calls.items():
    cl.sort()
    line, head, num, svc = trips[tid]
    seq = []
    for _, sid, mins, pu, do in cl:
        plat = stops.get(sid, {}).get("platform_code", "")
        seq.append([zi(sid), mins, plat, 1 if pu == "1" else 0, 1 if do == "1" else 0])
    out_trips.append([line, head, num, si(svc), seq])

days = {d: sorted(svc_idx[s] for s in ss if s in svc_idx) for d, ss in active.items()}
res = {"genere": dt.datetime.now().isoformat(timespec="minutes"), "source": "Île-de-France Mobilités (ODbL)", "jours": days, "zones": znames, "courses": out_trips}
os.makedirs(OUT, exist_ok=True)
txt = json.dumps(res, ensure_ascii=False, separators=(",", ":"))
if not out_trips:
    sys.exit("Aucune course extraite : fichier GTFS vide ou format inattendu, rien n'est publié.")
open(os.path.join(OUT, "horaires-ferres.json"), "w", encoding="utf-8").write(txt)
with gzip.open(os.path.join(OUT, "horaires-ferres.json.gz"), "wb", compresslevel=9) as f:
    f.write(txt.encode("utf-8"))
taille = os.path.getsize(os.path.join(OUT, "horaires-ferres.json")) / 1e6
print("Terminé :", len(out_trips), "courses,", len(znames), "gares,", NDAYS, "jours →", "horaires-ferres.json (%.1f Mo, %.1f Mo compressé)" % (taille, os.path.getsize(os.path.join(OUT, "horaires-ferres.json.gz")) / 1e6))
