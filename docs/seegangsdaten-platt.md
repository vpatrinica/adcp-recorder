# Seegangsdaten in Plattdütsch (Nipp un Nau för de Wetenschop)

Hier beschriewen wi, wat för Daten de ADCP-Recorder opteeken deit, wat in de enkelten Feller in steiht un woans dat allens sorteert is, dormit een dor ok orrig wat mit reken un forschen kann.

## NMEA Format un de Dateien

De Recorder kümmert sik dorüm, dat de Daten in dat **NMEA-Format** spiekert warrt. Dat sünd Text-Regeln, de jümmers mit en `$` anfangen doot un mit en Checksum (een Kuntroll-Tall, t.B. `*4A`) ophöört.
Tüschen de Weerten steiht jümmers en Komma. Weerten, de fehlen doot oder nich good sünd, warrt as **Sentinel-Weerten** wiest (süh ünnen).

### Checksum (Prüfsumm)
De Checksum is en **XOR** vun alle Bytes tüschen `$` un `*` (beer keen vun düsse twee). Dat Ergebnis warrt as twee Hex-Teken schrewen (t.B. `*4A`). Dormit kann man pröfen, of de Naricht heil ankommen is.

### Sentinel-Weerten (Invalid Data)
Wenn en Wert nich meten worrn is oder nich good is, warrt eine vun düsse Tahlen bruukt:

| Typ | Sentinel-Weerten |
|---|---|
| Ganztall (Integer) | `-9`, `-99`, `-999` |
| Kommatall (Float) | `-9.0`, `-99.0`, `-999.0` |

> **Tipp för Data Scientists:** Bi'n Inlesen mutt man düsse Weerten as `NaN` / `NULL` behandeln, sünst warrt de Statistik verdreht!

### De Ordner-Struktur (Daily Rotation)
För jeden Dag gifft dat ne'e Dateien. Dat nömt wi **Daily Rotation**. Dat süht so ut:

```
nmea/
├── PNORW/
│   ├── PNORW_20260305.nmea
│   └── PNORW_20260306.nmea
├── PNORWD/
│   └── PNORWD_20260305.nmea
├── PNORB/
│   └── PNORB_20260305.nmea
├── PNORE/
│   └── PNORE_20260305.nmea
└── PNORF/
    └── PNORF_20260305.nmea
```

**Schema:** `nmea/{TYP}/{TYP}_{YYYYMMDD}.nmea`
- `{TYP}` = Sentence-Typ (t.B. `PNORW`, `PNORB`)
- `{YYYYMMDD}` = Datum in ISO-Format ohn Streepen (t.B. `20260305` för 5. März 2026)

---

## De Daten-Typen (De "PNOR"-Familie)

Hier sünd de fief wichtigsten Bausteeen för de Seegangsdaten, mit all de Pöppen un Rinkiekers för de Wetenschop:

### 1. PNORW – De Hööft-Wellen-Maten (Wave Bulk Parameters)
Disse Naricht bargt all de grofften Statistiken över en Meet-Periood as een enkelten Satz.

**Format:** `$PNORW,Date,Time,Basis,Method,Hm0,H3,H10,Hmax,Tm02,Tp,Tz,DirTp,SprTp,MainDir,UI,MeanPress,NoDetect,BadDetect,NSurfSpeed,NSurfDir,ErrorCode*CS`

| Feld | Python-Naam | Wat dat is (Engelsch) | Typ | Eenheit | Bereich | Wat dat bedüüt |
|---|---|---|---|---|---|---|
| 0 | *(prefix)* | Prefix | str | - | `$PNORW` | Jümmers `$PNORW` |
| 1 | `date` | Date | str | MMDDYY | - | Meet-Datum (MaandDagJohr) |
| 2 | `time` | Time | str | hhmmss | - | Meet-Tiet (StünnMinuutSekunn) |
| 3 | `spectrum_basis` | Spectrum Basis | int | - | 0–3 | 0=Druck (Pressure), 1=Snelligkeit (Velocity), 3=AST |
| 4 | `processing_method` | Processing Method | int | - | 1–4 | 1=PUV, 2=SUV, 3=MLM, 4=MLMST |
| 5 | `hm0` | Significant Wave Height | float | m | 0–999.99 | De bedüdende Wellenhöögd (Hm0) |
| 6 | `h3` | Mean Top 1/3 | float | m | - | Dörsnitt vun de gröttsten Drüddel Wellen |
| 7 | `h10` | Mean Top 1/10 | float | m | - | Dörsnitt vun de gröttsten Teihntel Wellen |
| 8 | `hmax` | Max Wave Height | float | m | - | De allerhööchste Bülg in de Meet-Periood |
| 9 | `tm02` | Mean Wave Period | float | s | 0–999.99 | De Dörsnitts-Period vun de Wellen |
| 10 | `tp` | Peak Wave Period | float | s | 0–999.99 | De Hööft-Wellenperiod (wo de meiste Energie in sitt) |
| 11 | `tz` | Zero-crossing Period | float | s | - | De Nulldörgangs-Period |
| 12 | `dir_tp` | Peak Direction | float | ° | 0–360 | Richtung bi de Hööft-Period |
| 13 | `spr_tp` | Directional Spread at Peak | float | ° | 0–360 | Wo wiet de Wellen bi de Hööft-Period ut'neen fleegt |
| 14 | `main_dir` | Mean Direction | float | ° | 0–360 | De Dörsnitts-Richtung vun all Wellen |
| 15 | `uni_index` | Unidirectivity Index | float | - | - | Wo goot de Wellen ut een Richtung anrullt |
| 16 | `mean_pressure` | Mean Pressure | float | dBar | - | Dörsnitts-Druck in't Water |
| 17 | `num_no_detects` | No Detects | int | - | - | Wo faken nix sehn worrn is |
| 18 | `num_bad_detects` | Bad Detects | int | - | - | Wo faken de Metung tüdelig weer |
| 19 | `near_surface_speed` | Near Surf Speed | float | m/s | - | Stroomsnelligkeit boben ünner de Böverflach |
| 20 | `near_surface_dir` | Near Surf Dir | float | ° | - | Stroomrichtung boben |
| 21 | `wave_error_code` | Error Code | str | HEX | - | 4-stellige Hex-Tall för Fehlers, `0000` is allens kloor |

**Bispeel in de Praxis** *(Checksum `*XX` is en Platzholler)*:
```nmea
$PNORW,102115,090715,0,1,2.50,2.6,3.0,4.10,7.5,8.5,7.2,285.0,20.0,280.0,0.8,12.5,0,0,0.5,120.0,0000*XX
```
> **Optellt:** 22 Feller (mit `$PNORW`). Dat Datum `102115` = 21. Oktober 2015.

---

### 2. PNORWD – Wellen-Richtungen op Frequenzen (Wave Directional Spectra)
Hier geiht dat üm dat "Woher". Disse Satz harr een List an Frequenzen anhangt, un seggt för jede Frequenz wo de Wellen herkummt oder wo wiet se streit.

**Format:** `$PNORWD,DirType,Date,Time,Basis,Start,Step,Num,V1,V2,...,VN*CS`

> **Achtung:** Anders as bi PNORW gifft dat hier **keen `processing_method`** Feld! De Basis (Feld 4) folgt glieks op de Tiet.

| Feld | Python-Naam | Wat dat is (Engelsch) | Typ | Eenheit | Wat dat bedüüt |
|---|---|---|---|---|---|
| 0 | *(prefix)* | Prefix | str | - | `$PNORWD` |
| 1 | `direction_type` | Direction Type | str | `MD`/`DS` | **MD** = Main Direction (Hööftrichtung), **DS** = Directional Spread (Streuung) |
| 2 | `date` | Date | str | MMDDYY | Meet-Datum |
| 3 | `time` | Time | str | hhmmss | Meet-Tiet |
| 4 | `spectrum_basis` | Spectrum Basis | int | - | 0=Druck, 1=Snelligkeit, 3=AST *(keen Methode-Feld!)* |
| 5 | `start_frequency` | Start Frequency | float | Hz | Bi woveel Hertz fungen wi an (Bereich: 0–10) |
| 6 | `step_frequency` | Step Frequency | float | Hz | Sprung tüschen twee Pünkt (Bereich: 0–10) |
| 7 | `num_frequencies` | Num Frequencies | int | - | Wo veel Weerten (N) nu kaamt (1–999) |
| 8 … N+7 | `values[i]` | Direction / Spread | float | ° | De exakten Weerten (Richtung oder Streuung) för düsse Frequenz |

**Bispeel:**
```nmea
$PNORWD,MD,120720,093150,1,0.02,0.01,10,45.0,50.5,55.2,60.1,65.3,70.8,75.4,80.2,85.1,90.0*CS
```

> **Frequenz-Asse opbugen (Python):**
> ```python
> freqs = [start_frequency + i * step_frequency for i in range(num_frequencies)]
> ```

---

### 3. PNORB – Wellen in Frequenz-Bänner (Wave Band Parameters)
Hier snied de Recorder dat Spektrum in lüttere Bänner un gifft de Eckdaten jüst för düt lütte Stück (Band) ut. Kann de Seegang ut ünnerscheedlich Borns ut'neenhollen.

**Format:** `$PNORB,Date,Time,Basis,Method,FreqLow,FreqHigh,Hm0,Tm02,Tp,DirTp,SprTp,MainDir,ErrorCode*CS`

| Feld | Python-Naam | Wat dat is (Engelsch) | Typ | Eenheit | Bereich | Wat dat bedüüt |
|---|---|---|---|---|---|---|
| 0 | *(prefix)* | Prefix | str | - | `$PNORB` | Jümmers `$PNORB` |
| 1 | `date` | Date | str | MMDDYY | - | Meet-Datum |
| 2 | `time` | Time | str | hhmmss | - | Meet-Tiet |
| 3 | `spectrum_basis` | Spectrum Basis | int | - | 0–3 | Süh PNORW |
| 4 | `processing_method` | Processing Method | int | - | 1–4 | Süh PNORW |
| 5 | `freq_low` | Freq Low | float | Hz | 0–10 | Wo düt Band anfangt |
| 6 | `freq_high` | Freq High | float | Hz | 0–10 | Wo düt Band ophöört |
| 7 | `hm0` | Sig. Wave Height | float | m | 0–999.99 | Wellenhöögd man blot binnen düt Band |
| 8 | `tm02` | Mean Period | float | s | 0–999.99 | Dörsnitts-Period in düt Band |
| 9 | `tp` | Peak Period | float | s | 0–999.99 | Hööft-Period in düt Band |
| 10 | `dir_tp` | Peak Direction | float | ° | 0–360 | Richtung in düt Band |
| 11 | `spr_tp` | Spread at Peak | float | ° | 0–360 | Streuung in düt Band |
| 12 | `main_dir` | Mean Direction | float | ° | 0–360 | Dörsnitts-Richtung in düt Band |
| 13 | `wave_error_code` | Error Code | str | HEX | - | `0000` wenn kloor |

> **Optellt:** 14 Feller (mit `$PNORB`). Düt Sentence hett, liek as PNORW, ok en `processing_method`.

---

### 4. PNORE – Energie-Dicht (Wave Energy Density Spectrum)
Hier steiht in, wo veel "Wumm" (Energie) op jeder Frequenz in de See is. Düt is dat Spektrum an sik, worut Hm0 usw. utrekend warrt.

**Format:** `$PNORE,Date,Time,Basis,Start,Step,Num,E1,E2,...,EN*CS`

> **Achtung:** Anders as bi PNORW/PNORB gifft dat hier **keen `processing_method`** Feld!

| Feld | Python-Naam | Wat dat is (Engelsch) | Typ | Eenheit | Wat dat bedüüt |
|---|---|---|---|---|---|
| 0 | *(prefix)* | Prefix | str | - | `$PNORE` |
| 1 | `date` | Date | str | MMDDYY | Meet-Datum |
| 2 | `time` | Time | str | hhmmss | Meet-Tiet |
| 3 | `spectrum_basis` | Spectrum Basis | int | - | 0=Druck, 1=Snelligkeit, 3=AST *(keen Methode-Feld!)* |
| 4 | `start_frequency` | Start Frequency | float | Hz | Wo fungen wi an (Bereich: 0–10) |
| 5 | `step_frequency` | Step Frequency | float | Hz | Wo güng dat stapsvies vöran (Bereich: 0–10) |
| 6 | `num_frequencies` | Num Frequencies | int | - | Wo veel Weerten (N) nu kaamt (1–999) |
| 7 … N+6 | `energy_densities[i]` | Energy Density | float | cm²/Hz | De Energie för de enkele Frequenz. N-viele Weerten achter'nanner. |

> **Frequenz-Asse opbugen:** `freq[i] = start_frequency + i * step_frequency` för `i = 0 … N-1`

---

### 5. PNORF – Fourier-Koeffizienten (Fourier Coefficient Spectra)
Dat is wat för de Mathematikers un de deepere Wellen-Modell-Boer. Hier sünd de 4 Momente vun dat Spektrum för jede Frequenz anhangt.

**Format:** `$PNORF,Flag,Date,Time,Basis,Start,Step,Num,C1,C2,...,CN*CS`

| Feld | Python-Naam | Wat dat is (Engelsch) | Typ | Eenheit | Wat dat bedüüt |
|---|---|---|---|---|---|
| 0 | *(prefix)* | Prefix | str | - | `$PNORF` |
| 1 | `coefficient_flag` | Coefficient Flag | str | `A1`/`B1`/`A2`/`B2` | A1=1. Mom. Cosinus, B1=1. Mom. Sinus, A2=2. Mom. Cos, B2=2. Mom. Sin |
| 2 | `date` | Date | str | MMDDYY | Meet-Datum |
| 3 | `time` | Time | str | hhmmss | Meet-Tiet |
| 4 | `spectrum_basis` | Spectrum Basis | int | - | 0=Druck, 1=Snelligkeit, 3=AST *(keen Methode-Feld!)* |
| 5 | `start_frequency` | Start Frequency | float | Hz | Bi woveel Hertz fungen wi an (Bereich: 0–10) |
| 6 | `step_frequency` | Step Frequency | float | Hz | Sprung tüschen twee Pünkt (Bereich: 0–10) |
| 7 | `num_frequencies` | Num Frequencies | int | - | Wo veel Weerten (N) nu kaamt (1–999) |
| 8 … N+7 | `coefficients[i]` | Fourier Coefficient | float | - | Dat is de Mathematik-Tahl sülvst. N-viele achter'nanner. |

> **Optellt:** PNORF hett dat sülvige Layout as PNORWD, man mit `coefficient_flag` (A1/B1/A2/B2) ansteed vun `direction_type` (MD/DS).

---

## Dat Wichtigste kort un knapp:
1. **PNORW** gifft de Gesamtsicht (een Satz pro Meet-Zyklus, 22 Feller).
2. **PNORB** dröselt dat in Frequenz-Bänner op (Breden Seegang un Swünn trennt bekieken, 14 Feller).
3. **PNORE** bargt dat exakte Energie-Högen-Spektrum (variabel Tahl an Weerten).
4. **PNORWD & PNORF** vertellt di bit in de lüttste Frequenz de Richtungs-Eegenschapen in Graden un Fourier-Tahlen (variabel Tahl an Weerten).
5. Achte op dat Datum-Format vun de Amis (`MMDDYY` = Maand-Dag-Johr) **in de NMEA-Sentences**, nich mit us `DDMMYY` verquirlen!
6. Datei-Namen bruukt `YYYYMMDD` (ISO-Format): `PNORW_20260305.nmea`.

## Schnell-Referenz för Data Scientists

| Sentence | Feller | Hett Method? | Variabel? | Tofall |
|---|---|---|---|---|
| PNORW | 22 (fix) | ✅ Ja | Nee | Eeen Satz pro Meet-Zyklus |
| PNORB | 14 (fix) | ✅ Ja | Nee | Een Satz pro Frequenz-Band |
| PNORE | 7 + N | ❌ Nee | Ja | N = `num_frequencies` |
| PNORWD | 8 + N | ❌ Nee | Ja | N = `num_frequencies`, een Satz pro MD/DS |
| PNORF | 8 + N | ❌ Nee | Ja | N = `num_frequencies`, een Satz pro A1/B1/A2/B2 |

### Frequenz-Asse opbugen (für PNORE, PNORWD, PNORF):
```python
import numpy as np
freqs = start_frequency + np.arange(num_frequencies) * step_frequency
```

### Sentinel-Weerten filtern:
```python
SENTINELS = {-9, -99, -999, -9.0, -99.0, -999.0}
clean_value = np.nan if value in SENTINELS else value
```
