# Light meets Data #2: how OCT turns fringes into depth with a Fourier transform.
# Simulated spectral-domain OCT signal. A reflector at depth z makes fringes in the detected
# spectrum. The faster the fringes, the deeper the reflector. An FFT turns fringe speed into depth.
# The animation has four parts: one reflector, a moving reflector, two reflectors, a full image.
from pathlib import Path
import numpy as np
from scipy.signal import find_peaks
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.animation import FuncAnimation, PillowWriter, FFMpegWriter

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

# Number of fringes across the spectrum for a reflector at depth z: z * (k_end - k_start) / pi
def fringe_count(z):
    return z * (k_end - k_start) / np.pi

# 3. A simulated layered sample, scanned sideways (this becomes the OCT image)
# Five layers. In the middle of the scan they bend deeper, like a dip in the sample.
n_cols = 160
layer_base = [60, 100, 140, 185, 225]     # um
layer_dip = [30, 20, 8, 0, 0]             # how much each layer bends at the centre
layer_strength = [0.5, 0.35, 0.3, 0.4, 0.25]
rng = np.random.default_rng(3)            # fixed seed so the noise is repeatable

def layers_at(col):
    u = col / (n_cols - 1)
    dip = np.exp(-((u - 0.5) / 0.15) ** 2)
    tilt = 10 * np.sin(np.pi * u)
    return [b + d * dip + tilt for b, d in zip(layer_base, layer_dip)]

n_show = int(np.searchsorted(depth_axis, 300))     # only show depths up to 300 um
scan_spectra = []
image = np.zeros((n_show, n_cols))
for col in range(n_cols):
    spectrum = detected_spectrum(layers_at(col), layer_strength) + rng.normal(0, 0.05, n_points)
    scan_spectra.append(spectrum)
    image[:, col] = depth_profile(spectrum)[:n_show] / reference_peak

# 4. Checks printed to the terminal
for true_depth in (50, 100, 150, 200):
    spectrum = detected_spectrum([true_depth], [0.5])
    profile = depth_profile(spectrum)
    maxima = len(find_peaks(spectrum / source)[0])     # count the fringes by eye-like counting
    print(f"reflector at {true_depth:3d} um -> FFT peak at {depth_axis[profile.argmax()]:6.1f} um, "
          f"fringes: formula {fringe_count(true_depth):4.1f}, counted {maxima}")

centre = image[:, n_cols // 2]
found = depth_axis[:n_show][find_peaks(centre, height=0.1)[0]]
print("layers in the middle of the image (um):", np.round(found), " true:", np.round(layers_at(n_cols // 2)))

# The deepest depth we can measure: fringes faster than one cycle per two points cannot be sampled
print(f"deepest depth before aliasing: {np.pi / (2 * dk):.0f} um")

# 5. Animation frames (15 per second). Each frame says what to draw.
def smooth(t):
    return t * t * (3 - 2 * t)          # slow start, slow end

frames = []
def add(act, z1, s2=0.0, reveal=1.0, layout=0.0, col=-1):
    frames.append(dict(act=act, z1=z1, s2=s2, reveal=reveal, layout=layout, col=col))

for i in range(45):                                   # part 1: one reflector, depth hidden at first
    add(1, 50, reveal=np.clip((i - 24) / 8, 0, 1))
for t in np.linspace(0, 1, 90):                       # part 2: reflector moves deeper
    add(2, 50 + 150 * smooth(t))
for i in range(25):
    add(2, 200)
for t in np.linspace(0, 1, 30):                       # part 3: a second, weaker reflector appears
    add(3, 200, s2=0.6 * smooth(t))
for i in range(40):
    add(3, 200, s2=0.6)
for t in np.linspace(0, 1, 15):                       # part 4: switch to the image view
    add(4, 200, s2=0.6, layout=smooth(t))
for c in range(0, n_cols, 2):                         # scan sideways, one column at a time
    add(4, 200, s2=0.6, layout=1, col=c)
for i in range(50):
    add(4, 200, s2=0.6, layout=1, col=n_cols - 1)

captions = {
    1: "The detector records fringes, not depth.",
    2: "Deeper reflector = faster fringes = peak further right.",
    3: "Two reflectors: the fringes mix. The transform pulls them apart.",
    4: "Scan sideways and stack the depth profiles: an OCT image.",
}

# 6. Drawing
BG, FG, ACC, DIM, WARM = "#0E1513", "#E6EFEC", "#63D2C6", "#A9BDB8", "#F2B866"
# Use the Inter font if it is installed, otherwise matplotlib's default font
installed_fonts = {f.name for f in font_manager.fontManager.ttflist}
plt.rcParams["font.family"] = "Inter" if "Inter" in installed_fonts else "DejaVu Sans"
out = str(Path(__file__).parent) + "/"   # save the files next to this script
image_colors = LinearSegmentedColormap.from_list("oct", [BG, "#1B4A45", ACC, FG])

fig = plt.figure(figsize=(8, 8), dpi=135, facecolor=BG)
ax1 = fig.add_axes([0.13, 0.55, 0.82, 0.29])
ax2 = fig.add_axes([0.13, 0.13, 0.82, 0.26])
fig.text(0.10, 0.955, "An eye scan is a Fourier transform", color=FG, fontsize=21, weight="bold")
caption = fig.text(0.10, 0.912, "", color=DIM, fontsize=15)
fig.text(0.10, 0.015, "Simulated data and a simplified model.", color=DIM, fontsize=14)

# Panel positions: (top panel, bottom panel) for the line view and for the image view
line_view = ([0.13, 0.55, 0.82, 0.29], [0.13, 0.13, 0.82, 0.26])
image_view = ([0.13, 0.68, 0.82, 0.16], [0.13, 0.12, 0.82, 0.46])

def blend(a, b, t):
    return [x + (y - x) * t for x, y in zip(a, b)]

def style(ax):
    ax.set_facecolor(BG)
    ax.tick_params(colors=DIM, labelsize=13)
    for s in ax.spines.values():
        s.set_color(DIM)

def draw(i):
    f = frames[i]
    act, z1, s2 = f["act"], f["z1"], f["s2"]
    ax1.set_position(blend(line_view[0], image_view[0], f["layout"]))
    ax2.set_position(blend(line_view[1], image_view[1], f["layout"]))
    ax1.clear(); ax2.clear()
    image_mode = f["layout"] > 0

    # Which spectrum do we draw?
    if f["col"] >= 0:
        spectrum = scan_spectra[f["col"]]
    elif image_mode:
        spectrum = scan_spectra[0]
    else:
        depths, strengths = [z1], [0.5]
        if s2 > 0:
            depths.append(100)
            strengths.append(0.5 * s2)
        spectrum = detected_spectrum(depths, strengths)

    # top: what the detector records
    ax1.plot(k, spectrum, color=ACC, lw=1.2)
    ax1.set_xlim(k_start, k_end); ax1.set_ylim(0, 3.0 if image_mode else 2.1)
    ax1.set_ylabel("detected light", color=DIM, fontsize=14)
    if image_mode:
        ax1.set_title("What the detector records at this position", color=FG, fontsize=16, loc="left", pad=8)
    else:
        ax1.set_xlabel("wavenumber k (rad/µm)", color=DIM, fontsize=14)
        ax1.set_title("What the detector records: fringes", color=FG, fontsize=16, loc="left", pad=10)
    if act <= 2:
        ax1.text(0.02, 0.80, f"≈ {fringe_count(z1):.0f} fringes", transform=ax1.transAxes,
                 color=WARM, fontsize=19, weight="bold")

    # bottom: depth profile (parts 1 to 3) or the image (part 4)
    if image_mode:
        shown = np.zeros_like(image)
        last = f["col"] if f["col"] >= 0 else -1
        shown[:, : last + 1] = image[:, : last + 1]
        ax2.imshow(np.clip(shown, 0, 1) ** 0.6, extent=[0, n_cols, 300, 0], aspect="auto",
                   cmap=image_colors, vmin=0, vmax=1)
        if 0 <= last < n_cols - 1:
            ax2.axvline(last, color=WARM, lw=1.6)
        ax2.set_xlabel("scan position", color=DIM, fontsize=14)
        ax2.set_ylabel("depth (µm)", color=DIM, fontsize=14)
        ax2.set_title("Each column is one depth profile", color=FG, fontsize=16, loc="left", pad=8)
    else:
        ax2.set_xlim(0, 300); ax2.set_ylim(0, 1.7)
        ax2.set_xlabel("depth (µm)", color=DIM, fontsize=14)
        ax2.set_ylabel("reflection", color=DIM, fontsize=14)
        if f["reveal"] > 0:
            profile = depth_profile(spectrum) / reference_peak
            ax2.fill_between(depth_axis, profile, color=ACC, alpha=0.3 * f["reveal"])
            ax2.plot(depth_axis, profile, color=ACC, lw=1.6, alpha=f["reveal"])
            ax2.set_title("After a Fourier transform: depth", color=FG, fontsize=16, loc="left", pad=10)
            label = f"reflector at {z1:.0f} µm" if s2 == 0 else f"reflectors at 100 and {z1:.0f} µm"
            ax2.text(0.97, 0.80, label, transform=ax2.transAxes, color=WARM, fontsize=17, weight="bold", ha="right")
        else:
            ax2.set_title("Where is the reflector?", color=FG, fontsize=16, loc="left", pad=10)
            ax2.text(0.5, 0.5, "depth = ?", transform=ax2.transAxes, color=DIM, fontsize=30, ha="center", va="center")

    # caption: part 1 changes once the transform appears
    if act == 1 and f["reveal"] > 0:
        caption.set_text("A Fourier transform turns the fringes into depth.")
    else:
        caption.set_text(captions[act])
    style(ax1); style(ax2)

# 7. Save: an mp4 for LinkedIn (smooth) and a smaller gif for the README
anim = FuncAnimation(fig, draw, frames=len(frames), interval=1000 / 15)
anim.save(out + "fourier_oct.mp4", writer=FFMpegWriter(fps=15, codec="libx264",
          extra_args=["-pix_fmt", "yuv420p", "-crf", "20"]))

gif_frames = list(range(0, len(frames), 2))
anim_gif = FuncAnimation(fig, draw, frames=gif_frames, interval=1000 / 7.5)
anim_gif.save(out + "fourier_oct.gif", writer=PillowWriter(fps=7.5), dpi=80)
