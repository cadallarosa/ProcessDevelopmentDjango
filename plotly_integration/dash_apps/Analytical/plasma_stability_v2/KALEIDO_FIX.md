# Kaleido Installation Fix for PowerPoint Export

## Issue
You're seeing this warning:
```
Warning: You have Plotly version 6.0.0rc0, which is not compatible with this version of Kaleido (1.0.0).
This means that static image generation (e.g. `fig.write_image()`) will not work.
```

This prevents plots from appearing in the PowerPoint export.

## Solution

Run this command in your virtual environment:

```bash
pip uninstall kaleido
pip install kaleido==0.2.1
```

**OR** if you prefer to upgrade Plotly:

```bash
pip install --upgrade plotly
```

## Verify Installation

After installing, restart your Django server and test the PowerPoint export. You should see:
- ✓ Added plot for Plasma
- ✓ Added plot for Buffer

Instead of error messages.

## Alternative (if above doesn't work)

Try installing both with specific versions:

```bash
pip uninstall plotly kaleido
pip install plotly==5.18.0 kaleido==0.2.1
```
