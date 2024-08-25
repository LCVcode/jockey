# TODO: INFO FORMATS
TEMPLATE_ROFF = """
.SH NOTE
Jockey is a work-in-progress currently only supports querying:
.RS 4
- \\fBunits\\fR
- \\fBmachines\\fR
.RE

.SH FILTERS
Filters have a three-part syntax:

.B <OBJECT><FILTER><CONTENT>

.OBJECT can be any supported Juju object types or their equivalent abbreviations (see \\fBSHORT NAMES\\fR, below). These values are identical to the \\fBOBJECT\\fR argument in the Jockey CLI.

.FILTER specifies how objects should be filtered relative to \\fBCONTENT\\fR.
These are the possible values for \\fBFILTER\\fR:

.RS 4
{filters}
.RE

Exactly one \\fBFILTER\\fR must be given per filter.
\\fBCONTENT\\fR is a given string that will be used to filter Juju object names.

.SH SHORT NAMES
Jockey object name abbreviations:

.RS 4
{objects}
.RE

.SH EXAMPLES
.RS 4
.nf
.B juju-jockey units
get all units

.B juju-jockey units application=nova-compute
get all \\fBnova-compute\\fR units

.B juju-jockey u a=hw-health host~e01
get all \\fBhw-health\\fR units on hostname like "e01"

.B juju-jockey m m^~lxd
get all non-LXD machines
.RE
"""


def help_roff() -> str:
    TEMPLATE_ROFF.format()
