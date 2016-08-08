## About

`co_reader` (specifically `co_reader.get_co_date()`) is an implementation of a Certificate of Occupancy getter
which reads C-of-O data off of the New York City Department of Building's [BISweb](http://a810-bisweb.nyc.gov/bisweb/).

A Certificate of Occupancy is a document that a newly constructed (or heavily reconstructed) building receives that
certifies that it has been approved for residence. The issuance of a certificate of occupancy is traditionally the
end of a construction project proper.

The ability to turn a `BIN` (building identifier number, the DOB building indentifier) into a is-it-done-yet date
enables a whole range of things. See, for example, the [nyc-construction-timeline](https://github.com/ResidentMario/nyc-construction-timeline)
and [nyc-active-construction-sites](https://github.com/ResidentMario/nyc-active-construction-sites) repositories.