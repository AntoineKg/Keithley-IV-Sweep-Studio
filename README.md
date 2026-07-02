# Keithley I-V Sweep Studio

A responsive desktop GUI for dual-channel I-V sweeps with Keithley 2600 Series SourceMeter instruments.

## Download for Windows

<p align="center">
  <a href="https://github.com/AntoineKg/Keithley-IV-Sweep-Studio/releases/latest/download/Keithley-IV-Sweep-Studio.exe">
    <img src="https://img.shields.io/badge/DOWNLOAD_FOR_WINDOWS-2EA44F?style=for-the-badge&logo=windows11&logoColor=white" alt="Download Keithley I-V Sweep Studio for Windows" height="140">
  </a>
</p>

<p align="center"><strong>Standalone Windows application </strong></p>

Because the executable is not code-signed, Windows SmartScreen may ask you to confirm that you want to run it.

## Features

- Dual-channel voltage and current acquisition
- Responsive Tkinter interface with live progress and status updates
- Safe abort handling and output shutdown
- Input validation before outputs are enabled
- CSV export with timestamps and source setpoints
- Signed logarithmic current plots
- Support for ascending and descending sweeps without voltage overshoot

## Installation from source

Python 3.10 or newer is recommended.

```bash
python3 -m pip install -r requirements.txt
```

Tkinter is included with the standard Python installer on macOS and Windows. Linux users may need to install their distribution's `python3-tk` package.

## Running from source

```bash
python3 Keithley_IV_Sweep_Studio.py
```

Enter the instrument's IP address in the Connection panel, connect, review the sweep parameters, and start the sweep.

## Safety

This application can control equipment capable of hazardous voltage and current. Confirm that the selected limits are valid for your exact instrument model and test fixture. Use appropriate interlocks, shielding, grounding, and physical emergency-disconnect procedures. Software controls are not a substitute for laboratory safety systems.
