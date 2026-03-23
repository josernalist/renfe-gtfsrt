# renfe-gtfsrt

Archivador de datos GTFS Realtime de Renfe (Alta Velocidad, Larga y Media Distancia).

## Fuente

- **URL:** https://gtfsrt.renfe.com/trip_updates_LD.json
- **Formato:** GTFS-RT v2.0 (JSON)
- **Frecuencia de actualización:** cada 30 segundos (fuente), captura cada 5 minutos (este repo)

## Datos capturados

Cada fila del CSV diario contiene:

| Campo | Descripcion |
|---|---|
| `timestamp_utc` | Momento de la captura (UTC) |
| `trip_id` | ID del viaje (codigo tren + fecha) |
| `tren` | Codigo comercial del tren (5 digitos) |
| `fecha_tren` | Fecha del servicio |
| `estado` | `SCHEDULED` (circula) o `CANCELED` (cancelado) |
| `retraso_seg` | Retraso en segundos (solo si SCHEDULED) |
| `retraso_min` | Retraso en minutos (solo si SCHEDULED) |

## Estructura

```
data/YYYY/MM/gtfsrt-YYYY-MM-DD.csv
```

## Ejecucion

```bash
python scripts/fetch_gtfsrt.py
```
