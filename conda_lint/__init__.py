__version__ = "0.1.0"
__name__ = "conda-lint"
__author__ = "Jerimiah Willhite"
__email__ = "jwillhite@anaconda.com"
__license__ = "BSD-3-Clause"
__copyright__ = "Copyright (c) 2012, Anaconda, Inc."
__summary__ = __doc__
__url__ = "https://github.com/anaconda-distribution/conda-lint"
__summary__ = "A linter to make sure that a conda package meets SPDX standards before building it"
__long_description__ = """
This package's primary function is to make sure that a package has all of the 
correct metadata to create a valid SPDX-standard SBOM file. It may be extended
to make sure a package's file structure and metadata also conform to various
other package building standards as defined by the Anaconda build team.
"""

sub_commands = [
    'lint'
]