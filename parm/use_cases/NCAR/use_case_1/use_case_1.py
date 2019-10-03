"""
Some Descriptive Name Here
==========================

Are we missing this?
"""

import numpy as np
import xarray as xr

###############################################################################
# The file being rendered on this page is actually a ".py" file.
# 
# However, sphinx-gallery supports rendering RST from within a ".py" file.
#
# We can leverage the thumbnail-like gallery function of sphinx-gallery by writing RST in the example ".py" file.
#
# The advantage to this, is we can do things like incorporate static images:
#
# .. image:: ../../../../docs/_static/METplus_logo.png
#
# Or we can just write straight Python code:

#import os, subprocess

x = 1

my_list = ['Dan','George','Minna']

###############################################################################
# We can even use fancy LaTeX MATH stuff:
#
# .. math:: \sin (x)

for i in my_list:
  print("Name = ",i)

###############################################################################
# You can even reference other module/package documentation using intersphinx right within the use case ".py" file:
#
# But I can't seem to get this to work...
#
# I think in order to get this to work METplus has to be "importable"...which it is not currently.
#
# Possible answer `here <https://sphinx-gallery.github.io/configuration.html#link-to-documentation>`_

# Do we need a space here?
y = np.sin(x)

# How about here?
data = xr.open_dataset("test.nc")

###############################################################################
# 
# The file is essentially a hybrid Python/RST file

###############################################################################
#
# At the bottom of each PY file, we should include a ".. tip::" directive, and then include each MET tool.
# Example:
#
# .. note:: GridStatUseCase, PB2NCUseCase
#
# This will allow the "search bar" on the github.io page to find these pages, since the search bar only indexes things that are put into the HTML files.
