# Utils and Debug Scripts

This directory contains various utility scripts for verification, debugging, and sample data management.

## Contents

### Scripts

- **[verify_true_final_structure.py](file:///c:/prj/task/adcp-recorder/utils/verify_true_final_structure.py)**
    - A simulation script used to verify the consolidated storage structure for invalid records and binary blobs.
    - Confirms that `.dat` blobs go to `errors/binary/` and NMEA textual errors go to `errors/nmea/`.

- **[debug_wave_join.py](file:///c:/prj/task/adcp-recorder/utils/debug_wave_join.py)**
    - A debug tool used to analyze and verify the joining of multi-sentence wave records (e.g., PNORW).

- **[debug_amplitude.py](file:///c:/prj/task/adcp-recorder/utils/debug_amplitude.py)**
    - A utility script for debugging and visualizing amplitude data extracted from ADCP NMEA telemetry.

- **[debug_wave_alignment.py](file:///c:/prj/task/adcp-recorder/utils/debug_wave_alignment.py)**
    - A specialized script for verifying the alignment of wave parameters across multiple measurement families.

### Data

- **[adcp-data/](file:///c:/prj/task/adcp-recorder/utils/adcp-data)**
    - A directory containing sample ADCP telemetry files and recorded data used for testing and development.
