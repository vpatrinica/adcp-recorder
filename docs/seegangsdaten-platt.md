# Seegangsdaten in Plattdütsch (Nipp un Nau för de Wetenschop)

Hier beschriewen wi, wat för Daten de ADCP-Recorder opteeken deit, wat in de enkelten Feller in steiht un woans dat allens sorteert is, dormit een dor ok orrig wat mit reken un forschen kann.

## NMEA Format un de Dateien

De Recorder kümmert sik dorüm, dat de Daten in dat **NMEA-Format** spiekert warrt. Dat sünd Text-Regeln, de jümmers mit en `$` anfangen doot un mit en Checksum (een Kuntroll-Tall, t.B. `*CS`) ophöört. 
Tüschen de Weerten steiht jümmers en Komma. Weerten, de fehlen doot oder nich good sünd, warrt faken as `-9`, `-9.00` oder `-999` wiest. Dat is **Invalid Data**, dor mutt man bi oppassen.

För jeden Dag gifft dat en ne’en Ordner un niege Dateien. Dat nömt wi **Daily Rotation**.

### De Ordner-Struktur
Dat süht bi de Spiekeree so ut:
- `nmea/` – De Hauptpott för all dat NMEA-Gedööns.
    - `{Typ}/` – För jeden Daten-Typ en egen Fach (t.B. `PNORW`).
        - `{Typ}_{Datum}.nmea` – De Datei sülvst mit de Vörnaam (Typ) un Datum in’n Namen.

---

## De Daten-Typen (De "PNOR"-Familie)

Hier sünd de fief wichtigsten Bausteeen för de Seegangsdaten, mit all de Pöppen un Rinkiekers för de Wetenschop:

### 1. PNORW – De Hööft-Wellen-Maten (Wave Parameters)
Disse Naricht bargt all de grofften Statistiken över en Meet-Periood as een enkelten Satz.

| Feld | Naam (Platt) | Wat dat is (Engelsch) | Eenheit | Wat dat bedüüt |
|---|---|---|---|---|
| 0 | Vörteken | Prefix | - | Jümmers `$PNORW` |
| 1 | Datum | Date | MMDDYY | Meet-Datum (MaandDagJohr) |
| 2 | Tiet | Time | hhmmss | Meet-Tiet (StünnMinuutSekunn) |
| 3 | Spektrum-Grundlaag | Spectrum Basis | Typ | Woans de Wellen meet worrn sünd: 0=Druck (Pressure), 1=Snelligkeit (Velocity), 3=AST |
| 4 | Reken-Methood | Processing Method | Typ | 1=PUV, 2=SUV, 3=MLM, 4=MLMST |
| 5 | **Hm0** | Significant Wave Height | Meter (m) | De bedüdende Wellenhöögd |
| 6 | **H3** | Mean Top 1/3 | Meter (m) | Dörsnitt vun de gröttsten Drüddel Wellen |
| 7 | **H10** | Mean Top 1/10 | Meter (m) | Dörsnitt vun de gröttsten Teihntel Wellen |
| 8 | **Hmax** | Max Wave Height | Meter (m) | De allerhööchste Bülg in de Meet-Periood |
| 9 | **Tm02** | Mean Wave Period | Sekunnen (s) | De Dörsnitts-Period vun de Wellen |
| 10 | **Tp** | Peak Wave Period | Sekunnen (s) | De Hööft-Wellenperiod (wo de meiste Energie in sitt) |
| 11 | **Tz** | Zero-crossing Period | Sekunnen (s) | De Nulldörgangs-Period |
| 12 | **DirTp** | Peak Direction | Graad (°) | Richtung bi de Hööft-Period (0-360) |
| 13 | **SprTp** | Directional Spread at Peak | Graad (°) | Wo wiet de Wellen bi de Hööft-Period ut’neen fleegt |
| 14 | **MainDir** | Mean Direction | Graad (°) | De Dörsnitts-Richtung vun all Wellen |
| 15 | **UI** | Unidirectivity Index | - | Wo goot de Wellen ut een Richtung anrullt |
| 16 | Druck | Mean Pressure | dBar | Dörsnitts-Druck in't Water |
| 17 | Nich meten | No Detects | Tell | Wo faken nix sehn worrn is |
| 18 | Slecht meten | Bad Detects | Tell | Wo faken de Metung tüdelig weer |
| 19 | Stroom baven | Near Surf Speed | m/s | Stroomsnelligkeit boben ünner de Böverflach |
| 20 | Stroomricht baven | Near Surf Dir | Graad (°) | Stroomrichtung boben |
| 21 | Fehlerkood | Error Code | HEX | 4-stellige Hex-Tall för Fehlers `0000` is allens kloor |

**Bispeel in de Praxis:**
```nmea
$PNORW,102115,090715,0,1,2.50,2.6,3.0,4.10,7.5,8.5,7.2,285.0,20.0,280.0,0.8,12.5,0,0,0.5,120.0,0000*XX
```

---

### 2. PNORWD – Wellen-Richtungen op Frequenzen (Wave Directional Spectra)
Hier geiht dat üm dat "Woher". Disse Satz harr een List an Frequenzen anhangt, un seggt för jede Frequenz wo de Wellen herkummt oder wo wiet se streit.

| Feld | Naam (Platt) | Wat dat is (Engelsch) | Eenheit | Wat dat bedüüt |
|---|---|---|---|---|
| 1 | **Richtung-Typ** | Direction Type | `MD` / `DS` | **MD** = Main Direction (Hööftrichtung), **DS** = Directional Spread (Streuung) |
| ... | *Tiet & Spektrum (2-4)* | - | - | Süh PNORW |
| 5 | **Start-Frequenz** | Start Frequency | Hz | Bi wovell Hertz fungen wi an |
| 6 | **Schreed-Frequenz** | Step Frequency | Hz | Wo groot is de Sprung tüschen twee Pünkt |
| 7 | **Tahl Frequenzen** | Num Frequencies | Tell (N) | Wo veel Weerten nu kaamt |
| 8 - N+7 | **Richtung / Streu** | Direction / Spread | Graad (°) | De exakten Weerten (Richtung oder Streuung) för düsse Frequenz |

---

### 3. PNORB – Wellen in Frequenz-Bänner (Wave Band Parameters)
Hier snied de Recorder dat Spektrum in lüttere Bänner un gifft de Eckdaten jüst för düt lütte Stück (Band) ut. Kann de Seegang ut ünnerscheedlich Borns ut’neenhollen.

| Feld | Naam (Platt) | Wat dat is (Engelsch) | Eenheit | Wat dat bedüüt |
|---|---|---|---|---|
| ... | *Vörspann (0-4)* | - | - | Süh PNORW |
| 5 | **Unnerkant Freq.** | Freq Low | Hz | Wo düt Band anfangt |
| 6 | **Böverkant Freq.** | Freq High | Hz | Wo düt Band ophöört |
| 7 | **Hm0** (Band) | Sig. Wave Height | m | Wellenhöögd man blot binnen düt Band |
| 8 | **Tm02** (Band) | Mean Period | s | Dörsnitts-Period in düt Band |
| 9 | **Tp** (Band) | Peak Period | s | Hööft-Period in düt Band |
| 10 | **DirTp** (Band) | Peak Direction | Graad (°) | Richtung in düt Band |
| 11 | **SprTp** (Band) | Spread at Peak | Graad (°) | Streuung in düt Band |
| 12 | **MainDir** (Band) | Mean Direction | Graad (°) | Dörsnitts-Richtung in düt Band |
| 13 | *Fehlerkood* | Error Code | HEX | `0000` wenn kloor |

---

### 4. PNORE – Energie-Dicht (Wave Energy Density Spectrum)
Hier steiht in, wo veel "Wumm" (Energie) op jeder Frequenz in de See is. Düt is dat Spektrum an sik, worut Hm0 usw. utrekend warrt.

| Feld | Naam (Platt) | Wat dat is (Engelsch) | Eenheit | Wat dat bedüüt |
|---|---|---|---|---|
| ... | *Vörspann (0-3)* | - | - | Süh PNORW (keen Methode-Feld her, blots Basis) |
| 4 | **Start-Frequenz** | Start Frequency | Hz | Wo fungen wi an |
| 5 | **Schreed-Frequenz** | Step Frequency | Hz | Wo güng dat stapsvies vöran |
| 6 | **Tahl Frequenzen** | Num Frequencies | Tell (N) | Wo veel Weerten nu kaamt |
| 7 - N+6 | **Energie** | Energy Density | cm²/Hz | De Energie för de enkelte Frequenz. Hier kaamt glieks N-viele Weerten achter’nanner afrillt. |

---

### 5. PNORF – Fourier-Koeffizienten (Fourier Coefficient Spectra)
Dat is wat för de Mathematikers un de deepere Wellen-Modell-Boer. Hier sünd de 4 Momente vun dat Spektrum för jede Frequenz anhangt.

| Feld | Naam (Platt) | Wat dat is (Engelsch) | Eenheit | Wat dat bedüüt |
|---|---|---|---|---|
| 1 | **Typ vun Tall** | Coefficient Flag | `A1/B1/A2/B2` | A1=1. Mom. Cosinus, B1=1. Mom. Sinus, A2=2. Mom. Cos, B2=2. Mom. Sin |
| ... | *Vörspann & Freq* | - | - | Süh PNORWD aver mit düt Fiel |
| 8 - N+7 | **Koeffizient** | Fourier Coefficient | - (Tahl) | Dat is de Mathematik-Tahl sülvst. Ok hier N-viele achter’nanner wech. |

---

## Dat Wichtigste kort un knapp:
1. **PNORW** gifft de Gesamtsicht (een Satz pro Meet-Zyklus).
2. **PNORB** dröselt dat in Frequenz-Bänner op (Breden Seegang un Swünn trennt bekieken).
3. **PNORE** bargt dat exakte Energie-Högen-Spektrum. 
4. **PNORWD & PNORF** vertellt di bit in de lüttste Frequenz de Richtungs-Eegenschapen in Graden un Fourier-Tahlen.
5. Achte op dat Datum-Format vun de Amis (`MMDDYY` = Maand-Dag-Johr), nich mit us `DDMMYY` verquirlen!
