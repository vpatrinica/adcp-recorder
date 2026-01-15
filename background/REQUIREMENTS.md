
Technical specification and architecture and development plan for the adcp-recorder python project.

The software uses duckdb as backend.
it provides a cli/ controlplane and a supervised service running on windows/linux
and listening to a serial port and recording incoming data into duckdb.

The incoming data is assumed to be telemetry in the NMEA format with description following below, which is supposed to be printable ascii and crlf separated sentences of data, starting with $ and ending with *CHECKSUM; i want timestamped lines directly into duckdb;

the supervisor process makes sure the listener is active and performs a restart if necessary(configurable);

The cli/control plane can list com ports, can change the COMPORT to be listened to, the comport settings, data_report folder and can start/stop/restart the recorder.

the duckdb retains a table of the raw lines, in order, with a flag for parsed ok/fail, record_type(or ERROR) and will write a record into corresponding record table or error table.

EXTRA feature! all the payload are printable characters(except CRLF) and if the serial starts receiving binary.. the parser should detect after some number of characters like 1024 and instead switch into blob recording mode and make recording with timestamp in filename under ./data_folder/errors_binary/yyyymmdd_bin_identifier.dat instead of inserting into duckdb.

the user can configure, but by default gets data written into daily files per record_type: data_report/PNORI_2025_12_30.dat
data_report/PNORC_2025_12_30.dat
data_report/PNORS_2025_12_30.dat

data_report/PNORI1_2025_12_30.dat
data_report/PNORC1_2025_12_30.dat
data_report/PNORS1_2025_12_30.dat

data_report/PNORI2_2025_12_30.dat
data_report/PNORC2_2025_12_30.dat
data_report/PNORS2_2025_12_30.dat

data_report/PNORC3_2025_12_30.dat
data_report/PNORC4_2025_12_30.dat

this logs the received records by type and date of the recording

Format details of the sentences:
valid_prefixes=[PNORC, PNORS, PNORI, PNORC1, PNORI1, PNORS1, PNORC2, PNORI2, PNORS2, PNORA, PNORW,PNORH3,PNORS3,PNORC3,PNORH4,PNORS4,PNORC4, PNORW, PNORB, PNORE, PNORF,PNORWD]

The sentence is composed of a comma separated list of columns, starting with a valid prefix, and then continuing with 1) either a list (fixed or variable length depending on the prefix) of values like decimal, number, characters depending on the position in the sequence and prefix.
or 2) a list of  key=value comma separated pairs.
the end of the sentence is marked with * and followed by 2 bytes checksum.

The checksum calculation is part of the NMEA standard. It is the representation of two hexadecimal characters of an XOR if all characters in the sentence between – but not including – the $ and the * character.
It is expected that crlf is following the checksum, before a new sentence, however crlfs could appear redundantly or not be present, so the parsing should not rely on those.
• Data with variants of -9 (-9.00, -999…) are invalid data.

Naive implementation of the main process:

```python
init_setup:
   init_logging()
   init_rx_buffer()
   init_fifo()
   test_output_folder(fallback=./data folder in the application root folder)
   configure_duckdb()
   connect_to_duckdb()
   configure_serial()
   connect_to_serial()
   non_nmea_rx_counter=0
   non_nmea_cons_recs=0
   carry_over_payload=””

fifo_producer_loop:
            
    heartbeat_fifo_producer()
    check_on_rx()
    while receive_buffer not empty:
         receive-line-or-chuck(max length 2048 or CRLF)
         fill_fifo(append to end)
    sleep()
    
fifo_consumer_loop:
     heartbeat_fifo_consumer()
     check_fifo()
     if not empty fifo:
         payload= fifo.pop()
         payload = (carry_over_payload + payload)
         find_nmea_id() // find first comma
         //match yo
         find_checksum_sep()
         find_checksum_value()
         find_prefix_checksum()
         
        
         non_nmea_chars = scan_for_nonnmea(payload)
         // if non_nmea_chars>MAX_NON_NMEA_CHARS_PER_LINE
         process()

def process(buffer):
     //TODO: parse_sentence..
```

## Key Features

- Asynchronous serial polling with automatic reconnection
- NMEA checksum validation and frame parsing
- duckdb line persistence (timestamp-based) as raw line with parsed flag
- Graceful signal handling and clean shutdown
- Health monitoring with optional webhook alerting
- Per-append mode for safe inter-process file handoff
- Structured tracing to stderr (pluggable collectors)
- Cross-platform binary with platform-specific service templates

FOLLOWING IS THE SPECIFICATION OF THE NMEA SENTENCES

EXAMPLES
Information Data
PREFIXES: PNORI, PNORI1, PNORI2

Example:

$PNORI,4,Signature1000900001,4,20,0.20,1.00,0*2E
Example (with tags):

$PNORI1,4,123456,4,30,1.00,5.00,BEAM*5B

Example (without tags):

$PNORI2,IT=4,SN=123456,NB=4,NC=30,BD=1.00,CS=5.00,CY=BEAM*68

Header Data
PREFIXES: PNORH3, PNORH4
Example (with tags):

$PNORH3,DATE=141112,TIME=081946,EC=0,SC=2A4C0000*5F

Example (without tags):

$PNORH4,141112,083149,0,2A4C0000*4A68

Sensors Data
PREFIXES: PNORS, PNORS1, PNORS2, PNORS3, PNORS4

Follows a previously transmitted Information Data(PNORI) with CY setting

$PNORS,102115,090715,00000000,2A480000,14.4,1523.0,275.9,15.7,2.3,0.000,22.
45,0,0*1C

Example (with tags):

$PNORS2,DATE=083013,TIME=132455,EC=0,SC=34000034,BV=22.9,SS=1500.0,HSD=0.02,H=123.4,PI=45.6,PISD=0.02,R=23.4,RSD=0.02,P=123.456,PSD=0.02,T=24.56*3F

Example (without tags):

$PNORS1,083013,132455,0,34000034,22.9,1500.0,0.02,123.4,45.6,0.02,R=23.4,0.02,123.456,0.02,24.56*39

Follows a previously transmitted Header Data(PNORH3/PNORH4) with timestamp
Example (with tags):

$PNORS3,BV=22.9,SS=1546.1,H=151.1,PI=-12.0,R=-5.2,P=705.669,T=24.96*7A

Example (without tags):

$PNORS4,22.9,1546.1,151.2,-11.9,-5.3,705.658,24.95*5A

Averaged Data
PREFIXES: PNORC, PNORC1, PNORC2, PNORC3, PNORC4

$PNORC,102115,090715,4,0.56,-0.80,-1.99,-1.33,0.98,305.2,C,80,88,67,78,13,17,10,18*22

Follows a previously transmitted Information Data(PNORI/PNORI1/PNORI2) with CY setting
Example (with tags, CY=ENU):

$PNORC2,DATE=083013,TIME=132455,CN=3,CP=11.0,V1=0.332,V2=0.332,V3=-
0.332,V4=-0.332,A1=78.9,A2=78.9,A3=78.9,A4=78.9,C1=78,C2=78,C3=78,C4=78*49

Example (without tags CY=ENU):

$PNORC1,083013,132455,3,11.0,0.332,0.332,0.332,0.332,78.9,78.9,78.9,78.9,78
,78,78,78*46

Follows a previously transmitted Header Data(PNORH3/PNORH4) with timestamp
Example (with tags):

$PNORC3,CP=4.5,SP=3.519,DIR=110.9,AC=6,AA=28*3B

Example (without tags):

$PNORC4,27.5,1.815,322.6,4,28*70

Altimeter
PREFIXES: PNORA
Example (format without Tags):

$PNORA,190902,122341,0.000,24.274,13068,08,-2.6,-0.8*7E
Example (format with Tags):

$PNORA,DATE=190902,TIME=122341,P=0.000,A=24.274,Q=13068,ST=08,PI=-2.6,R=-0.8*72

Waves
PREFIXES: PNORW, PNORB, PNORF, PNORWD
Example Wave parameters:

$PNORW,120720,093150,0,1,0.89,-9.00,1.13,1.49,1.41,1.03,-9.00,190.03,80.67,113.52,0.54,0.00,1024,0,1.19,144.11,0D8B*7B
Example Wave band parameters:

$PNORB,120720,093150,1,4,0.02,0.20,0.27,7.54,12.00,82.42,75.46,82.10,0000*67
$PNORB,120720,093150,1,4,0.21,0.99,0.83,1.36,1.03,45.00,0.00,172.16,0000*5C

Example Fourier coefficient spectra:

$PNORF,A1,120720,093150,1,0.02,0.01,98,0.0348,0.0958,0.1372,0.1049,-0.0215,-
0.0143,0.0358,0.0903,0.0350,0.0465,-0.0097,0.0549,-0.0507,-0.0071,-0.0737,0.0459,-0.0164,0.0275,-0.0190,-0.0327,-0.0324,-0.0364,-0.0255,-0.0140,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000*0D

$PNORF,B1,120720,093150,1,0.02,0.01,98,-0.0230,-0.0431,0.0282,0.0151,0.0136,0.0465,0.1317,0.1310,0.0500,0.0571,0.0168,0.0713,-0.0002,0.0164,-0.0315,0.0656,-0.0046,0.0364,-0.0058,0.0227,0.0014,0.0077,0.0017,0.0041,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000*2F

$PNORF,A2,120720,093150,1,0.02,0.01,98,-0.3609,-0.0617,0.0441,0.0812,-0.0956,-0.1695,-0.3085,-0.2760,-0.2235,-0.1159,-0.0956,-0.0421,-0.0474,0.0119,0.0079,-0.0578,-0.1210,-0.1411,-0.0939,-0.1063,-0.1158,-0.1201,-0.1393,-0.1556,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000*26

$PNORF,B2,120720,093150,1,0.02,0.01,98,0.6465,0.3908,0.3669,0.3364,0.6169,0.6358,0.6473,0.6038,0.5338,0.4258,0.3862,0.3817,0.3692,0.2823,0.1669,0.1052,0.0019,-0.1209,-0.2095,-0.2144,-0.2109,-0.2509,-0.2809,-0.3491,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000*07

Example Wave directional spectra:

$PNORWD,MD,120720,093150,1,0.02,0.01,98,326.5016,335.7948,11.6072,8.1730,147.6098,107.1336,74.8001,55.4424,55.0203,50.8304,120.0490,52.4414,180.2204,113.3304,203.1034,55.0302,195.6657,52.9780,196.9988,145.2517,177.5576,168.0439,176.1304,163.7607,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000*05

$PNORWD,DS,120720,093150,1,0.02,0.01,98,79.3190,76.6542,75.1406,76.6127,79.9920,79.0342,75.2961,74.3028,78.5193,77.9860,80.2380,77.2964,78.9473,80.3010,77.7126,77.7154,80.3341,79.1574,80.2208,79.4005,79.7031,79.5054,79.9868,80.4341,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000*16
