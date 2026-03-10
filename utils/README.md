# Utils and Debug Scripts

This directory contains various utility scripts for verification, debugging, and sample data management.

## Contents

### Scripts

- **[ftp_sync.py](file:///c:/prj/adcp-recorder/utils/ftp_sync.py)**
    - Rsync-like FTP mirror script. Uploads changed files from local `nmea/`, `db/`, and `parquet/` subdirectories to a remote FTP server.
    - Supports CLI arguments and environment variables (`FTP_HOST`, `FTP_USER`, `FTP_PASS`) for credentials.
    - Features: size-based change detection, glob exclusion patterns, dry-run mode, verbose logging.
    - Usage: `python ftp_sync.py -H ftp.example.com -u user -p pass --dry-run`
    - See also: systemd service/timer templates in `adcp_recorder/templates/linux/`.

- **[verify_true_final_structure.py](file:///c:/prj/task/adcp-recorder/utils/verify_true_final_structure.py)**
    - A simulation script used to verify the consolidated storage structure for invalid records and binary blobs.
    - Confirms that `.dat` blobs go to `errors/binary/` and NMEA textual errors go to `errors/nmea/`.

- **[duckdb_diagnostics.py](file:///c:/prj/task/adcp-recorder/utils/duckdb_diagnostics.py)**
    - Reusable utility to list objects, search metadata SQL, and find table dependencies.

- **[debug_wave_join.py](file:///c:/prj/task/adcp-recorder/utils/debug_wave_join.py)**
    - A debug tool used to analyze and verify the joining of multi-sentence wave records (e.g., PNORW).

- **[debug_amplitude.py](file:///c:/prj/task/adcp-recorder/utils/debug_amplitude.py)**
    - A utility script for debugging and visualizing amplitude data extracted from ADCP NMEA telemetry.

- **[debug_wave_alignment.py](file:///c:/prj/task/adcp-recorder/utils/debug_wave_alignment.py)**
    - A specialized script for verifying the alignment of wave parameters across multiple measurement families.

### Data

- **[adcp-data/](file:///c:/prj/task/adcp-recorder/utils/adcp-data)**
    - A directory containing sample ADCP telemetry files and recorded data used for testing and development.
