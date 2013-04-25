Congressional Tenure Tracker
===============

# Data
The data for current and former lawmakers comes from the excellent [United States project](https://github.com/unitedstates/congress-legislators) on GitHub.

## Dependencies
pyaml

## Retrieval and formatting
To retrieve and format the data, run:

    ./scripts/tenure.py
    
This will download the data from Github, convert it to JSON (which can take awhile) and calculate the tenure for each
session of congress. See the comments in the python source for details.
