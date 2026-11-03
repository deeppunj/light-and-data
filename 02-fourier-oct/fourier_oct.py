# Light meets Data #2: how OCT turns fringes into depth with a Fourier transform.
# Simulated spectral-domain OCT signal. A reflector at depth z makes fringes in the detected
# spectrum. The faster the fringes, the deeper the reflector. An FFT turns fringe speed into depth.
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.animation import FuncAnimation, PillowWriter

# 1. The simulated instrument
# The detector records the light spectrum at N wavenumbers k (k = 2 * pi / wavelength).
# Here: wavelengths from 800 to 880 nm, written in micrometres (um).
n_points = 1024
k_start = 2 * np.pi / 0.880      # rad/um
k_end = 2 * np.pi / 0.800        # rad/um
k = np.linspace(k_start, k_end, n_points, endpoint=False)
dk = k[1] - k[0]                 # step between two neighboring k values

# The light source has a smooth bell-shaped spectrum S(k)
k_centre = k.mean()
k_width = (k_end - k_start) / 5
source = np.exp(-(k - k_centre) ** 2 / (2 * k_width ** 2))

# 2. Signal and Fourier transform
def detected_spectrum(depths, strengths):
    """What the detector sees: the source spectrum with a fringe pattern for each reflector."""
    fringes = sum(a * np.cos(2 * k * z) for z, a in zip(depths, strengths))
    return source * (1 + fringes)

# Zero-padding (more points in the FFT) only makes the peaks smoother to draw
n_fft = 8192
depth_axis = np.pi * np.arange(n_fft // 2) / (n_fft * dk)   # um. Bin number -> depth.

def depth_profile(spectrum):
    """FFT of the fringes (the spectrum minus the source background) gives the signal vs depth."""
    fringes_only = spectrum - source
    return np.abs(np.fft.fft(fringes_only, n_fft))[: n_fft // 2]

# Scale so that one reflector with fringe strength 0.5 gives a peak of height 1
reference_peak = depth_profile(detected_spectrum([100], [0.5])).max()

# 3. Checks printed to the terminal
for true_depth in (40, 100, 150, 220):
    profile = depth_profile(detected_spectrum([true_depth], [0.5]))
    print(f"reflector at {true_depth:3d} um -> FFT peak at {depth_axis[profile.argmax()]:6.1f} um")

# The deepest depth we can measure: fringes faster than one cycle per two points cannot be sampled
print(f"deepest depth before aliasing: {np.pi / (2 * dk):.0f} um")

# 4. Animation frames: (depth of reflector 1, depth of reflector 2, strength of reflector 2)
frames = []
for z1 in np.linspace(40, 220, 28):          # reflector 1 moves deeper
    frames.append((z1, 200, 0.0))
for z1 in np.linspace(220, 100, 10):         # and comes back
    frames.append((z1, 200, 0.0))
for s2 in np.linspace(0, 0.6, 8):            # a second reflector appears, weaker
    frames.append((100, 200, s2))
frames += [(100, 200, 0.6)] * 12             # hold the last frame

# 5. Drawing
BG, FG, ACC, DIM, WARM = "#0E1513", "#E6EFEC", "#63D2C6", "#A9BDB8", "#F2B866"
# Use the Inter font if it is installed, otherwise matplotlib's default font
installed_fonts = {f.name for f in font_manager.fontManager.ttflist}
plt.rcParams["font.family"] = "Inter" if "Inter" in installed_fonts else "DejaVu Sans"
out = str(Path(__file__).parent) + "/"   # save the images next to this script

fig = plt.figure(figsize=(8, 8), dpi=135, facecolor=BG)
ax1 = fig.add_axes([0.13, 0.55, 0.82, 0.29])
ax2 = fig.add_axes([0.13, 0.13, 0.82, 0.26])
fig.text(0.10, 0.955, "An eye scan is a Fourier transform", color=FG, fontsize=21, weight="bold")
fig.text(0.10, 0.912, "Simulated OCT signal: fringes go in, depth comes out.", color=DIM, fontsize=15)
fig.text(0.10, 0.015, "Faster fringes = deeper reflector. The FFT reads the fringe speed.", color=DIM, fontsize=14)

def style(ax):
    ax.set_facecolor(BG)
    ax.tick_params(colors=DIM, labelsize=13)
    for s in ax.spines.values():
        s.set_color(DIM)

def draw(i):
    z1, z2, s2 = frames[i]
    depths, strengths = [z1], [0.5]
    if s2 > 0:
        depths.append(z2)
        strengths.append(0.5 * s2)
    spectrum = detected_spectrum(depths, strengths)
    profile = depth_profile(spectrum) / reference_peak

    ax1.clear(); ax2.clear()
    # top: what the detector records
    ax1.plot(k, spectrum, color=ACC, lw=1.2)
    ax1.set_xlim(k_start, k_end); ax1.set_ylim(0, 2.1)
    ax1.set_xlabel("wavenumber k (rad/µm)", color=DIM, fontsize=14)
    ax1.set_ylabel("detected light", color=DIM, fontsize=14)
    ax1.set_title("What the detector records: fringes", color=FG, fontsize=16, loc="left", pad=10)
    # bottom: after the Fourier transform
    ax2.fill_between(depth_axis, profile, color=ACC, alpha=0.3)
    ax2.plot(depth_axis, profile, color=ACC, lw=1.6)
    ax2.set_xlim(0, 300); ax2.set_ylim(0, 1.7)
    ax2.set_xlabel("depth (µm)", color=DIM, fontsize=14)
    ax2.set_ylabel("reflection", color=DIM, fontsize=14)
    ax2.set_title("After a Fourier transform: depth", color=FG, fontsize=16, loc="left", pad=10)
    if s2 > 0:
        label = f"reflectors at {z1:.0f} and {z2:.0f} µm"
    else:
        label = f"reflector at {z1:.0f} µm"
    ax2.text(0.97, 0.80, label, transform=ax2.transAxes, color=WARM, fontsize=17, weight="bold", ha="right")
    style(ax1); style(ax2)

anim = FuncAnimation(fig, draw, frames=len(frames), interval=100)
anim.save(out + "fourier_oct.gif", writer=PillowWriter(fps=10))
