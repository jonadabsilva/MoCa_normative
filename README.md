# MoCA Normative Calculator

This is a web application built in R/Shiny designed to calculate normalized Z-scores and percentiles for the Montreal Cognitive Assessment (MoCA). 

The normative data driving this calculator is strictly sourced from:
**Rossetti, H. C., Lacritz, L. H., Cullum, C. M., & Weiner, M. F. (2011). Normative data for the Montreal Cognitive Assessment (MoCA) in a population-based sample. *Neurology*, 77(13), 1272-1275.**

## Features
* **Individual Assessment**: Select a patient's age bracket and education tier to calculate standard scores based on published means and standard deviations. Generates a visual probability density plot.
* **Batch Processing**: Upload a CSV of raw scores to automatically calculate and export expected parameters, Z-scores, and classifications for an entire dataset at once.

## Usage
To run this app locally, ensure you have R installed along with the required libraries:
```R
install.packages(c("shiny", "ggplot2", "dplyr", "readr", "lubridate"))