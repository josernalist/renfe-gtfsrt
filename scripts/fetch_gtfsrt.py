#!/usr/bin/env python3
"""
Renfe GTFS-RT Archiver
Descarga https://gtfsrt.renfe.com/trip_updates_LD.json
y añade los datos al CSV diario en data/YYYY/MM/gtfsrt-YYYY-MM-DD.csv

Cada captura registra: timestamp, trip_id, tren, fecha_tren, estado, retraso_seg, retraso_min
Solo escribe filas nuevas si el contenido ha cambiado respecto a la captura anterior.
"""

import os
import csv
import json
import hashlib
import urllib.request
import datetime
import sys
import time

GTFSRT_URL = "https://gtfsrt.renfe.com/trip_updates_LD.json"

COLUMNAS = [
    "timestamp_utc",
    "trip_id",
    "tren",
    "fecha_tren",
    "estado",
    "retraso_seg",
    "retraso_min",
]


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def fetch() -> bytes:
    req = urllib.request.Request(
        GTFSRT_URL,
        headers={
            "User-Agent": "renfe-gtfsrt-archiver/1.0",
            "Accept": "application/json, */*",
        },
        method="GET",
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                if resp.status != 200:
                    raise RuntimeError(f"HTTP {resp.status}")
                return resp.read()
        except Exception as e:
            if attempt == 2:
                print(f"ERROR tras 3 intentos: {e}", file=sys.stderr)
                sys.exit(1)
            print(f"Intento {attempt + 1} fallido: {e}. Reintentando...", file=sys.stderr)
            time.sleep(5)


def last_hash_path(out_dir: str) -> str:
    return os.path.join(out_dir, ".last_hash_gtfsrt")


def load_last_hash(out_dir: str):
    p = last_hash_path(out_dir)
    return open(p).read().strip() if os.path.exists(p) else None


def save_hash(out_dir: str, h: str):
    with open(last_hash_path(out_dir), "w") as f:
        f.write(h)


def parse_trip_id(trip_id: str) -> tuple:
    """Extrae tren (5 digitos) y fecha del trip_id.
    Formato: TTTTTNYYYY-MM-DD (tren 5 dig + variante 1 dig + fecha)
    Ej: '0408712026-03-23' -> ('04087', '2026-03-23')
    """
    import re
    tren = trip_id[:5]
    m = re.search(r"(\d{4}-\d{2}-\d{2})$", trip_id)
    fecha = m.group(1) if m else trip_id[6:]
    return tren, fecha


def append_csv(out_path: str, timestamp_utc: str, entities: list):
    file_exists = os.path.exists(out_path)
    with open(out_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNAS)
        if not file_exists:
            writer.writeheader()
        for entity in entities:
            trip_update = entity.get("tripUpdate", {})
            trip = trip_update.get("trip", {})
            trip_id = trip.get("tripId", "")
            schedule = trip.get("scheduleRelationship", "SCHEDULED")
            delay_seg = trip_update.get("delay", 0) if schedule != "CANCELED" else ""

            tren, fecha_tren = parse_trip_id(trip_id)

            delay_min = ""
            if delay_seg != "":
                delay_min = round(int(delay_seg) / 60, 1)

            writer.writerow({
                "timestamp_utc": timestamp_utc,
                "trip_id": trip_id,
                "tren": tren,
                "fecha_tren": fecha_tren,
                "estado": schedule,
                "retraso_seg": delay_seg,
                "retraso_min": delay_min,
            })


def main():
    now_utc = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
    out_dir = os.path.join("data", now_utc.strftime("%Y"), now_utc.strftime("%m"))
    os.makedirs(out_dir, exist_ok=True)

    data = fetch()
    h = sha256(data)

    if load_last_hash(out_dir) == h:
        print("Sin cambios respecto a la captura anterior. No se escriben filas.")
        sys.exit(0)

    parsed = json.loads(data)
    header = parsed.get("header", {})
    entities = parsed.get("entity", [])
    timestamp_utc = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

    # CSV diario
    csv_filename = f"gtfsrt-{now_utc.strftime('%Y-%m-%d')}.csv"
    csv_path = os.path.join(out_dir, csv_filename)

    append_csv(csv_path, timestamp_utc, entities)
    save_hash(out_dir, h)

    n_scheduled = sum(1 for e in entities if e.get("tripUpdate", {}).get("trip", {}).get("scheduleRelationship") == "SCHEDULED")
    n_canceled = sum(1 for e in entities if e.get("tripUpdate", {}).get("trip", {}).get("scheduleRelationship") == "CANCELED")

    print(f"CSV        : {csv_path}")
    print(f"Timestamp  : {timestamp_utc}")
    print(f"Feed TS    : {header.get('timestamp', '?')}")
    print(f"Entidades  : {len(entities)} (activos={n_scheduled}, cancelados={n_canceled})")


if __name__ == "__main__":
    main()
