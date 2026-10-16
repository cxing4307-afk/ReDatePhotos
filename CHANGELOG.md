# Changelog

## v0.1.0 — 2026-10-16

- Read JPEG capture dates from EXIF with a modified-time fallback.
- Preview deterministic chronological filenames and resolve matching timestamps.
- Apply collision-safe batch renames and undo the latest completed operation.
- Skip damaged images without stopping the rest of a scan.
- Add a local single-page Flask interface and a synthetic demo set.
