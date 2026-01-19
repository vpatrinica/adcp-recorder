import os
import shutil
from pathlib import Path
from adcp_recorder.export.file_writer import FileWriter
from adcp_recorder.export.binary_writer import BinaryBlobWriter

def verify_paths():
    test_base = Path("test_output")
    if test_base.exists():
        shutil.rmtree(test_base)
    
    os.makedirs(test_base)
    
    print(f"Testing with base path: {test_base.absolute()}")
    
    # Test FileWriter.write_invalid_record (Non-binary, known prefix)
    fw = FileWriter(str(test_base))
    fw.write_invalid_record("PNORI", "Some invalid PNORI data")
    
    # Test FileWriter.write_invalid_record (Binary marker)
    fw.write_invalid_record("BINARY", "Some binary textual error record\r\n")
    
    # Test FileWriter.write_invalid_record (Unknown prefix)
    fw.write_invalid_record("UNKNOWN_THING", "Some random error data\r\n")
    
    # Test BinaryBlobWriter (Handles ONLY binary content in errors/binary)
    bw = BinaryBlobWriter(str(test_base))
    bw.start_blob(b"\x00\x01\x02")
    bw.finish_blob()
    
    print("\nChecking directory structure:")
    for root, dirs, files in os.walk(test_base):
        level = root.replace(str(test_base), '').count(os.sep)
        indent = ' ' * 4 * level
        if os.path.basename(root):
            print(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            print(f"{subindent}{f}")

    # Assertions
    errors_dir = test_base / "errors"
    binary_dir = errors_dir / "binary"
    nmea_dir = errors_dir / "nmea"
    
    assert errors_dir.exists(), "errors directory missing"
    assert binary_dir.exists(), "errors/binary directory missing"
    assert nmea_dir.exists(), "errors/nmea directory missing"
    
    # Check binary folder (ONLY blobs)
    binary_files = list(binary_dir.glob("*"))
    print(f"\nFiles in errors/binary: {[f.name for f in binary_files]}")
    assert any(f.suffix == '.dat' for f in binary_files), "Missing .dat file in errors/binary"
    assert not any(f.suffix == '.nmea' for f in binary_files), "Found .nmea file in errors/binary, expected ONLY .dat blobs"
    
    # Check nmea folder (ALL textual errors)
    nmea_files = list(nmea_dir.glob("*.nmea"))
    print(f"Files in errors/nmea/: {[f.name for f in nmea_files]}")
    assert any("PNORI_error_" in f.name for f in nmea_files), "Missing PNORI_error_*.nmea in errors/nmea/"
    assert any(f.name.startswith("ERROR_") for f in nmea_files), "Missing consolidated ERROR_*.nmea in errors/nmea/"
    
    # Verify content of consolidated error file
    error_file = [f for f in nmea_files if f.name.startswith("ERROR_")][0]
    content = error_file.read_text()
    assert "binary textual error record" in content, "Missing binary marker in ERROR_*.nmea"
    assert "random error data" in content, "Missing unknown prefix data in ERROR_*.nmea"
    
    print("\nFinal Verification SUCCESSFUL!")
    # shutil.rmtree(test_base)

if __name__ == "__main__":
    try:
        verify_paths()
    except Exception as e:
        print(f"\nVerification FAILED: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
