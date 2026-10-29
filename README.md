# Light meets Data

Short teaching posts for scientists and engineers moving into data work. Each post takes one idea, from optics, measurement or statistics, and shows it in a picture or a short animation. Every folder here holds the Python code behind one post, so you can run it and change it.

All data in this repo is simulated, so the true answer is known and you can see how close the method gets.

## Posts

| # | Topic | Folder |
|---|---|---|
| 1 | Averaging noisy scans: standard error σ/√N | [01-standard-error](01-standard-error) |
| 2 | Fourier transform: how OCT sees depth | coming |
| 3 | When averaging fails: speckle | coming |

## Run a post

```
conda create -n light-and-data python=3.11
conda activate light-and-data
pip install -r requirements.txt
python 01-standard-error/standard_error.py
```

The images are saved in the post's own folder.

## Author

Deep Punj, PhD. Optical engineer at Ghent University, working on lasers, OCT and imaging data with Python and SQL.
