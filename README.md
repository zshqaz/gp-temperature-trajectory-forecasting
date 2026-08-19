# Gaussian-process forecasting of London July temperatures

This repository contains the source code for a UK MSc dissertation on how covariance-kernel specification affects the predictive accuracy and uncertainty calibration of Gaussian-process models that forecast the remaining London July temperature trajectory after observations through 09:00 local time.

The analysis uses hourly ERA5-Land 2 m temperature at latitude 51.5, longitude 0.0. July days from 1940--2025 are represented as replicated 24-hour curves. Evaluation is rolling-origin by year for 2001--2025. The main probabilistic target is the temperature trajectory from 10:00--23:00; the daily post-09:00 maximum is a secondary derived target.


