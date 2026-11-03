# 2. How OCT turns fringes into depth: the Fourier transform

In optical coherence tomography (OCT) the detector records light across many wavelengths. A reflector at depth z makes fringes (wavy interference patterns) in that spectrum, and the deeper it is, the faster the fringes. A Fourier transform (FFT) reads the fringe speed and gives the depth. Do this at every position along the sample, stack the results, and you have an OCT image.

![Animation](fourier_oct.gif)

The animation has four parts:

1. One reflector. The detector only sees fringes. The FFT turns them into a depth.
2. The reflector moves deeper. The fringe count goes up (about 0.23 fringes per µm of depth) and the peak moves right.
3. A second, weaker reflector appears. The fringes mix, and the FFT separates them into two peaks.
4. Scan sideways, and stack the depth profiles into an image of a layered sample.

## What the code does

1. Simulates a spectrometer: 1024 wavenumbers k for wavelengths from 800 to 880 nm, and a bell-shaped light source.
2. Builds the detected spectrum: the source spectrum with one fringe pattern per reflector.
3. Subtracts the source background and takes the FFT. Bin number is turned into depth with z = π · bin / (n_fft · Δk).
4. Simulates a sample with five bending layers, 160 scan positions and a little noise, and turns every position into a column of the image.
5. Prints checks: the FFT peak lands on the true depth, the fringe count matches the formula, and all five layers are found.

| True depth | FFT peak | Fringes (formula / counted) |
|---|---|---|
| 50 µm | 50.0 µm | 11.4 / 11 |
| 100 µm | 100.1 µm | 22.7 / 22 |
| 150 µm | 150.1 µm | 34.1 / 34 |
| 200 µm | 200.2 µm | 45.5 / 45 |

A weaker reflector gives a smaller peak (0.6 times as high in the animation).

## Run it

```
python fourier_oct.py
```

This writes `fourier_oct.mp4` (for posting) and `fourier_oct.gif` (small, for this page) next to the script. It needs ffmpeg for the mp4. It takes a couple of minutes. Try changing `layer_base` or `n_points` near the top.

## Limit

The deepest depth you can measure is π / (2 · Δk), here about 2250 µm. Deeper reflectors make fringes too fast to sample, and their peaks wrap back to the wrong depth. This is aliasing, the topic of a later post (Nyquist).

The signal is simulated and simplified: one clean reflection per layer, no dispersion, a little random noise in the image part.
