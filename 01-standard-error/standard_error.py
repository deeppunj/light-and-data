# Light meets Data #1: averaging noisy scans, and how sure are you of the result?
# Simulated depth profile (like an OCT A-scan). Every scan has independent random noise.
# Statistics part: estimate the height of the first layer and give a 95% confidence interval.
from pathlib import Path
import numpy as np
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.animation import FuncAnimation, PillowWriter

rng = np.random.default_rng(7)  # fixed seed so the result is repeatable

# 1. The "true" signal: three reflecting layers at different depths ---
depth = np.linspace(0, 1, 400)

def layer(center, width, height):
    return height * np.exp(-((depth - center) / width) ** 2)

true_signal = layer(0.25, 0.02, 1.0) + layer(0.50, 0.02, 0.7) + layer(0.75, 0.02, 0.5)

# 2. 100 scans = true signal + independent random noise (sigma = 1)
n_scans = 100
noise_sigma = 1.0
scans = true_signal + rng.normal(0, noise_sigma, (n_scans, depth.size))

# 3. The quantity we want: height of the first layer (one depth pixel at its peak)
peak = np.argmax(true_signal)
true_height = true_signal[peak]
readings = scans[:, peak]  # one noisy reading of that height per scan

def estimate(n):
    """Mean of the first n readings and the half-width of its 95% confidence interval."""
    x = readings[:n]
    mean = x.mean()
    if n < 2:
        return mean, np.nan
    sem = x.std(ddof=1) / np.sqrt(n)            # standard error of the mean
    half = stats.t.ppf(0.975, n - 1) * sem       # t-value because n is small
    return mean, half

all_n = np.arange(1, n_scans + 1)
est = np.array([estimate(n) for n in all_n])
means, halves = est[:, 0], est[:, 1]

# Check printed to the terminal: width of the interval shrinks as 1/sqrt(N)
for n in [4, 16, 64, 100]:
    print(f"N={n:3d}  estimate={means[n-1]:5.2f}  95% CI = +-{halves[n-1]:.2f}")
# Sample size needed for +-0.2 when sigma = 1:  n = (1.96 * sigma / 0.2)^2
print("scans needed for +-0.2:", round((1.96 * noise_sigma / 0.2) ** 2))

# 4. Frames: slow at the start, then faster, then hold the last one
frames = list(range(2, 11)) + list(range(12, 31, 2)) + list(range(35, 101, 5)) + [100] * 12

# 5. Drawing
BG, FG, ACC, DIM, WARM = "#0E1513", "#E6EFEC", "#63D2C6", "#A9BDB8", "#F2B866"
# Use the Inter font if it is installed, otherwise matplotlib's default font
installed_fonts = {f.name for f in font_manager.fontManager.ttflist}
plt.rcParams["font.family"] = "Inter" if "Inter" in installed_fonts else "DejaVu Sans"
out = str(Path(__file__).parent) + "/"  # save the images next to this script

def style(ax):
    ax.set_facecolor(BG)
    ax.tick_params(colors=DIM, labelsize=13)
    for s in ax.spines.values():
        s.set_color(DIM)

fig = plt.figure(figsize=(8, 8), dpi=135, facecolor=BG)
ax1 = fig.add_axes([0.13, 0.55, 0.82, 0.29])
ax2 = fig.add_axes([0.13, 0.13, 0.82, 0.26])
fig.text(0.10, 0.945, "Why 100 noisy scans beat one good scan", color=FG, fontsize=20, weight="bold")
fig.text(0.10, 0.895, "Simulated data. Average more scans, and know how sure you are.", color=DIM, fontsize=15)
fig.text(0.10, 0.012, "Standard error = σ/√N. Same rule in A/B tests and surveys.", color=DIM, fontsize=14)

def draw(i):
    n = frames[i]
    ax1.clear(); ax2.clear()
    # top: average of n scans vs the true signal
    ax1.plot(depth, scans[:n].mean(axis=0), color=ACC, lw=1.3, label=f"average of {n} scans")
    ax1.plot(depth, true_signal, color=FG, lw=1, ls="--", alpha=0.7, label="true signal")
    ax1.axvline(depth[peak], color=WARM, lw=0.8, alpha=0.6)
    ax1.set_ylim(-4, 5); ax1.set_xlim(0, 1)
    ax1.set_xlabel("depth", color=DIM, fontsize=14)
    ax1.set_ylabel("signal", color=DIM, fontsize=14)
    ax1.text(depth[peak] + 0.015, 3.4, "layer we measure", color=WARM, fontsize=14)
    ax1.legend(loc="upper right", frameon=False, labelcolor=FG, fontsize=14)
    ax1.text(0.02, 0.76, f"N = {n}", transform=ax1.transAxes, color=FG, fontsize=28, weight="bold")
    # bottom: estimate of that layer's height with its 95% confidence band
    k = np.arange(1, n + 1)
    ax2.axhline(true_height, color=FG, lw=1, ls="--", alpha=0.7, label="true value (1.0)")
    ax2.fill_between(all_n[1:n], (means - halves)[1:n], (means + halves)[1:n], color=ACC, alpha=0.25, label="95% confidence range")
    ax2.plot(all_n[:n], means[:n], color=ACC, lw=1.5, label="our estimate")
    ax2.set_title("How sure are we of that layer's height?", color=FG, fontsize=16, loc="left")
    ax2.set_xlim(0, 100); ax2.set_ylim(-2.5, 5.5)
    ax2.set_xlabel("number of scans averaged (N)", color=DIM, fontsize=14)
    ax2.set_ylabel("height of that layer", color=DIM, fontsize=14)
    ax2.legend(loc="upper right", frameon=False, labelcolor=FG, fontsize=13)
    if n >= 2:
        ax2.text(0.02, 0.08, f"uncertainty ±{halves[n-1]:.2f}", transform=ax2.transAxes, color=WARM, fontsize=22, weight="bold")
    style(ax1); style(ax2)

anim = FuncAnimation(fig, draw, frames=len(frames), interval=150)
anim.save(out + "standard_error.gif", writer=PillowWriter(fps=7))

# 6. Static before/after image (N = 1 vs N = 100)
fig2, (a, b) = plt.subplots(2, 1, figsize=(8, 8), dpi=135, facecolor=BG, sharex=True)
fig2.subplots_adjust(left=0.13, right=0.94, top=0.80, bottom=0.14, hspace=0.25)
fig2.text(0.10, 0.94, "Same sample. Same instrument.", color=FG, fontsize=25, weight="bold")
fig2.text(0.10, 0.895, "Only the number of averaged scans changes (simulated data)", color=DIM, fontsize=15)
for ax, n in ((a, 1), (b, 100)):
    ax.plot(depth, scans[:n].mean(axis=0), color=ACC, lw=1.2)
    ax.plot(depth, true_signal, color=FG, lw=0.8, ls="--", alpha=0.6)
    ax.set_ylim(-4, 5)
    style(ax)
    label = "1 scan: layer height unknown (±1.0 per reading)" if n == 1 else f"100 scans: height {means[-1]:.2f} ± {halves[-1]:.2f} (95% CI)"
    ax.text(0.02, 0.86, label, transform=ax.transAxes, color=FG, fontsize=17, weight="bold")
b.set_xlabel("depth", color=DIM, fontsize=14)
fig2.text(0.10, 0.015, "Standard error = σ/√N: 4× the data = half the uncertainty.", color=DIM, fontsize=14)
fig2.savefig(out + "before_after.png", facecolor=BG)
