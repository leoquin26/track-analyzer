# Keyflow

*Sets that flow in key.* (formerly Track Analyzer)

Build DJ-friendly sets from a folder of songs. Keyflow analyzes each track for **BPM**, **musical key**, **Camelot code**, **rhythm/groove**, and **energy**, then suggests the best order to mix them.

Think of it as a basic **Mixed In Key + set optimizer**.

---

## What you need

- **Python 3.10 or newer** ([download](https://www.python.org/downloads/))
- **Windows, macOS, or Linux**
- A folder with audio files (`.mp3`, `.wav`, `.flac`, `.m4a`, `.aac`, `.ogg`)

During Python installation on Windows, check **"Add Python to PATH"**.

---

## Quick start (dashboard — recommended)

### 1. Get the project

Copy the project folder to your computer, or clone it:

```bash
git clone <repository-url>
cd track_analyzer
```

### 2. Install dependencies

Open a terminal in the project folder and run:

```bash
pip install -r requirements.txt
```

### 3. Start the dashboard

**Windows — double-click:**

```
run_dashboard.bat
```

**Or from terminal:**

```bash
python -m streamlit run dashboard.py
```

Your browser should open at **http://localhost:8501**.

### 4. Analyze your music

1. Click **Browse music folder** and select the folder with your tracks.
2. Optionally change the **output folder** (where results are saved).
3. Choose **analysis length**:
   - *First 3 minutes* — fast, good for most sets
   - *First 5 minutes* — a bit more accurate
   - *Full track* — slowest, best for long tracks or unusual intros
4. Toggle **Include subfolders** if your music is in nested folders.
5. Click **Analyze & Build Playlist**.

When finished, you will see:

- Suggested playlist order (cards)
- Transition score charts
- BPM vs energy map
- Compatibility heatmap
- Download buttons for CSV and M3U files

---

## Command line (optional)

If you prefer the terminal instead of the dashboard:

```bash
python harmonic_playlist.py "C:\path\to\your\music\folder"
```

**Useful flags:**

```bash
# Scan subfolders
python harmonic_playlist.py "C:\Music\DJ Set" -r

# Analyze full tracks (not just first 3 minutes)
python harmonic_playlist.py "C:\Music\DJ Set" -d 0

# Save output to a specific folder
python harmonic_playlist.py "C:\Music\DJ Set" -o "C:\Music\output"
```

---

## Output files

After analysis, these files are created in your output folder:

| File | Description |
|------|-------------|
| `track_analysis.csv` | BPM, key, Camelot, energy, and onset rate for every track |
| `playlist_order.csv` | Suggested mix order with transition scores |
| `transition_matrix.csv` | Pairwise transition scores between all tracks |
| `playlist.m3u` | Playlist file you can import into DJ software |

### Example playlist row

```csv
order,title,bpm,key,camelot,energy,transition_score_from_previous
1,Track A,122.5,Am,8A,-21.4,
2,Track B,123.8,Em,9A,-20.8,87.2
```

---

## Try it with test tracks (no music library needed)

Generate 3 sample WAV files and run a quick test:

```bash
python generate_test_tracks.py
python harmonic_playlist.py test_tracks -o test_output -d 30
```

Or open the dashboard and point it at the `test_tracks` folder.

---

## How transitions are scored

Each transition between two tracks is scored using:

| Factor | What it measures |
|--------|------------------|
| **Harmonic** | Camelot key compatibility (same key, relative major/minor, adjacent wheel) |
| **BPM** | Tempo difference |
| **Rhythm** | Groove similarity (onset/beat pattern) |
| **Onset** | Percussive density match |
| **Energy** | Loudness/energy flow |

Two tracks can share the same Camelot key but still score low if their grooves differ (e.g. straight tech-house vs afro percussive).

---

## Project structure

```
track_analyzer/
├── dashboard.py           # Web dashboard (main way to use the app)
├── harmonic_playlist.py   # Core analysis + playlist logic
├── generate_test_tracks.py # Optional sample tracks for testing
├── run_dashboard.bat      # Windows launcher
├── requirements.txt       # Python dependencies
└── README.md              # This guide
```

---

## Troubleshooting

### `python` is not recognized

Python is not on your PATH. Reinstall Python and enable **"Add Python to PATH"**, or use:

```bash
py -m pip install -r requirements.txt
py -m streamlit run dashboard.py
```

### `streamlit` is not recognized

Use the module form:

```bash
python -m streamlit run dashboard.py
```

### No audio files found

- Check that the folder path is correct.
- Enable **Include subfolders** if tracks are in nested directories.
- Supported formats: `.mp3`, `.wav`, `.flac`, `.m4a`, `.aac`, `.ogg`.

### Some tracks fail to analyze

Corrupt files, DRM-protected downloads, or unsupported encodings can fail. Check the error list in the dashboard, or run the CLI to see per-file errors in the terminal.

### Browse folder button does nothing (macOS/Linux)

The native folder picker uses Tkinter. On Linux you may need:

```bash
sudo apt install python3-tk   # Debian/Ubuntu
```

You can always type the folder path manually in the text field.

### Analysis is slow

- Use **First 3 minutes** instead of full track.
- Fewer files = faster runs.
- First run may be slower while libraries initialize.

### Import / dependency errors

Reinstall dependencies:

```bash
pip install -r requirements.txt --upgrade
```

---

## Sharing this project with a friend

1. Zip the project folder (or share the Git repo).
2. Tell them to install **Python 3.10+**.
3. Send them to this README — **Quick start** is enough to get running.

They do **not** need your music files or previous analysis output. Only the project code and their own track folder.

---

## Important note

This tool helps organize a set using technical data. It does **not** replace listening with your ears. Key detection can be wrong, and vocals, drops, intros/outros, and mood still matter for real DJ transitions.

**Recommended workflow:**

1. Run the automatic analysis.
2. Review the suggested order.
3. Test transitions manually before a live set.
