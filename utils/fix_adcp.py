"""
Fuer den Fall, dass der Workaround ueber die Computerzeit notwendg wird:
Aendere den Importstring von "from datetime import datetime"
in "from datetime import datetime, timezone"
Aendere die Funktion "def get_current_time():" in:
    posix_time = datetime.now(timezone.utc).timestamp()
    ntp_time = datetime.utcfromtimestamp(posix_time)
    print(f"Aktuelle NTP-Zeit: {ntp_time.strftime(DATE_FORMAT)}")
    return ntp_time

Dies gilt, wenn der Server die reine POSIX-Timestamp zur Verfuegung stellt.
Wenn es die LOKALE ZEIT ist, dann bleibt die Klammer von "now()" einfach leer.
"""

import os
import threading
import time
from datetime import datetime
from time import sleep

import serial

# Konfiguration
SERIAL_PORT = "COM6"  # COM-Port auf COM2 geändert
BAUD_RATE = 9600
TIMEOUT = 1
NTP_SERVER = "pool.ntp.org"
DOWNLOAD_PATH = r"C:\DATA"  # Pfad für das Speichern der Datei
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FILENAME_FORMAT = "%Y-%m-%d"


# Funktion zum Anzeigen der ankommenden Daten von der seriellen Schnittstelle
def monitor_serial_data(ser):
    print("Starte Überwachung der seriellen Schnittstelle...")
    while True:
        if ser.in_waiting > 0:
            data = ser.read(ser.in_waiting).decode(errors="ignore")
            print(f"Empfangene Daten: {data}")
        time.sleep(0.01)  # Kleine Pause, um die CPU-Auslastung gering zu halten


# Funktion zum Senden des spezifizierten BREAK-Signals
def send_break_signal(ser):
    print("Sende spezifiziertes BREAK-Signal...")

    # Schritt 1: Sende @@@@@@
    ser.write(b"@@@@@@")
    print("Gesendet: @@@@@@")

    # Schritt 2: Wartezeit von 150 ms + 50 % (225 ms)
    time.sleep(0.225)

    # Schritt 3: Sende K1W%!Q
    ser.write(b"K1W%!Q")
    print("Gesendet: K1W%!Q (nach 225 ms)")

    # Schritt 4: Wartezeit von 400 ms + 50 % (600 ms)
    time.sleep(0.6)

    # Schritt 5: Sende K1W%!Q erneut
    ser.write(b"K1W%!Q")
    print("Gesendet: K1W%!Q (nach 600 ms)")


# Funktion zum Senden und Empfangen von Befehlen an das Messgerät
def send_command(ser, command, expect_responses=None):
    """
    Sendet einen Befehl an das Gerät und prüft, ob die erwarteten Antworten empfangen werden.
    """
    if isinstance(expect_responses, str):
        expect_responses = [expect_responses]
    elif expect_responses is None:
        expect_responses = []

    print(f"Sende Befehl: {command}")
    ser.write(f"{command}\r\n".encode())  # Befehl senden
    start_time = time.time()  # Startzeit für das Warten auf Daten

    response = ""  # Variable für die gesamte Antwort

    # Lese Daten, solange die maximale Wartezeit (2 Sekunden) noch nicht vergangen ist
    while time.time() - start_time < 2:
        if ser.in_waiting > 0:  # Daten sind verfügbar
            response += ser.read(ser.in_waiting).decode(errors="ignore")

    print(f"Empfangene Daten (Rohdaten): {repr(response)}")  # Zeige empfangene Rohdaten

    # Bereinige die Antwort von allen Steuerzeichen (\r, \n, etc.)
    response_cleaned = response.replace("\r", "").replace("\n", "").strip()

    print(f"Bereinigte Antwort: {repr(response_cleaned)}")

    # Sonderbehandlung für den TMSTAT-Befehl
    if command == "TMSTAT":
        # Extrahiere die Zahl und das 'OK' separat
        if "OK" in response_cleaned:
            number_part = response_cleaned.split("OK")[0].strip()
            response_cleaned = number_part  # Nur die Zahl behalten
        print(f"Bereinigte Antwort nach Sonderbehandlung für TMSTAT: {response_cleaned}")

    # Prüfe auf die erwarteten Antworten
    responses_found = set()
    for expected in expect_responses:
        if expected in response_cleaned:
            responses_found.add(expected)

    # Überprüfen, ob alle erwarteten Antworten empfangen wurden
    if len(responses_found) == len(expect_responses):
        print("Alle erwarteten Antworten empfangen.")
        print(f"Vollständige Antwort (bereinigt): {response_cleaned}")
        return response_cleaned
    else:
        missing_responses = set(expect_responses) - responses_found
        print(f"Fehlende Antworten: {missing_responses}")
        print(f"Vollständige Antwort (bereinigt): {response_cleaned}")
        raise ValueError(
            f"Erwartete Antworten {missing_responses} nicht erhalten. Antwort: '{response_cleaned}'"
        )


# Funktion zum Abrufen der aktuellen Zeit vom NTP-Server
def get_current_time():
    posix_time = datetime.now().timestamp()
    ntp_time = datetime.utcfromtimestamp(posix_time)
    print(f"Aktuelle NTP-Zeit: {ntp_time.strftime(DATE_FORMAT)}")
    return ntp_time


# Funktion zum Erstellen eines Dateinamens mit aktuellem Datum
def get_filename():
    current_date = datetime.now().strftime(DATE_FILENAME_FORMAT)
    filename = os.path.join(DOWNLOAD_PATH, f"Telemetrie_{current_date}.txt")
    return filename


# Funktion zum Überprüfen und Erstellen des Download-Ordners
def check_and_create_directory(path):
    if not os.path.exists(path):
        print(f"Ordner '{path}' existiert nicht. Erstelle Ordner...")
        os.makedirs(path)
    else:
        print(f"Ordner '{path}' existiert bereits.")


# Funktion zum Abrufen und Speichern der Telemetriedaten in 4096-Byte-Chunks
# Funktion zum Abrufen der Telemetriedaten
def download_telemetry_data(ser, file_size):
    start_address = 0
    chunk_size = 4096
    filename = get_filename()

    print(f"Datei wird gespeichert unter: {filename}")

    with open(filename, "wb") as file:
        while start_address < file_size:
            command = f"DOWNLOADTM,SA={start_address},LEN={chunk_size},CKS=1"
            response = send_command(ser, command, ["OK"])  # Hier erwarten wir "OK" als Antwort

            # Hier filtern wir die Binärdaten heraus, die nach "OK" kommen
            # Wir müssen sicherstellen, dass die Antwort die erwarteten Daten enthält
            if "OK" in response:
                # Extrahiere nur die Binärdaten, die nach "OK" kommen
                binary_data = extract_binary_data(response)
                file.write(binary_data)
            else:
                print(f"Fehler: Die Antwort auf den Befehl '{command}' war nicht wie erwartet.")
                break

            start_address += chunk_size
            sleep(1)  # Pause, um die Datenübertragung nicht zu überlasten

    print(f"Telemetrie-Daten erfolgreich gespeichert unter: {filename}")


# Funktion zum Extrahieren der Binärdaten
def extract_binary_data(response):
    binary_data_start = response.find("OK") + len("OK")  # Finde den Punkt nach "OK"
    binary_data = response[binary_data_start:]  # Extrahiere den Rest der Antwort als Binärdaten
    return binary_data.encode()  # Rückgabe als Bytearray


# Funktion für den ERASETM-Befehl
def erase_telemetry_data(ser):
    command = "ERASETM,9999"
    response = send_command(ser, command, ["OK"])

    if "OK" in response:
        print("Telemetrie-Daten erfolgreich gelöscht.")
    else:
        print(f"Fehler beim Löschen der Telemetrie-Daten. Antwort: {response}")


# Hauptprogramm
def main():

    try:
        # Seriellen Port öffnen
        print("Versuche, seriellen Port zu öffnen...")
        ser = serial.Serial(SERIAL_PORT, baudrate=BAUD_RATE, timeout=TIMEOUT)
        print(f"Serieller Port {SERIAL_PORT} erfolgreich geöffnet.")

        # Starte Überwachung der seriellen Schnittstelle in einem separaten Thread
        monitor_thread = threading.Thread(target=monitor_serial_data, args=(ser,))
        monitor_thread.daemon = True
        monitor_thread.start()

        send_break_signal(ser)

        send_command(ser, "% Send Break", ["CONFIRM", "OK"])
        send_command(ser, "MC", "OK")

        send_command(ser, "SETDEFAULT,ALL", "OK")
        send_command(
            ser,
            'SETPLAN,MIAVG=600,AVG=0,DIAVG=0,VD=0,MV=10,SA=35,BURST=1,MIBURST=1800,DIBURST=0,SV=0,FN="lkn04.ad2cp",SO=0,FREQ=1000,NSTT=0',
            "OK",
        )
        send_command(
            ser,
            'SETBURST,NC=22,NB=4,CS=0.4,BD=3.5,CY="BEAM",PL=0,SR=2,NS=2048,VR=2.5,DF=3,NPING=7,CH=0,VR5=2.5,ALTI=1,BT=0,DISV=0,ECHO=0,RAWALTI=1,ALTISTART=0.1,ALTIEND=21.2,HR=0,HR5=0',
            "OK",
        )
        send_command(
            ser,
            'SETWAVEPROC,EN=1,MOUNTHEIGHT=0.5,MODE="MLMST",BANDSEPFREQ=0.2,FREQSTART=0.02,FREQEND=0.99,FREQSTEP=0.01',
            "OK",
        )
        send_command(ser, "SETTMWAVE,EN=1,DF=501,TWAP=1,TEDS=1,TWBS=1,TFS=1,SO=1,FO=1,TWDR=1", "OK")
        send_command(ser, "SAVE,ALL", "OK")
        # current_time = get_current_time()
        # command = (
        #     f"SETCLOCK,YEAR={current_time.year},MONTH={current_time.month},"
        #     f"DAY={current_time.day},HOUR={current_time.hour+1},"
        #     f"MINUTE={current_time.minute},SECOND={current_time.second}"
        # )
        # send_command(ser, command, "OK")

        send_command(ser, "START", "OK")

        print("Warte 30 Sekunden bis Ende")
        sleep(30)

    except PermissionError as e:
        print(f"Zugriffsfehler: {e}. Warte 1 Stunde und versuche es erneut...")
        sleep(60)  # 1 Stunde warten und dann erneut versuchen
    except Exception as e:
        print(f"Fehler: {e}")
        sleep(60)  # 1 Stunde warten und dann erneut versuchen


if __name__ == "__main__":
    main()
