## About

`co_reader` (specifically `co_reader.get_co_date()`) is an implementation of a Certificate of Occupancy getter
which reads C-of-O data off of the New York City Department of Building's [BISweb](http://a810-bisweb.nyc.gov/bisweb/).

A Certificate of Occupancy is a document that a newly constructed (or heavily reconstructed) building receives that
certifies that it has been approved for residence. The issuance of a certificate of occupancy is traditionally the
end of a construction project proper.

The ability to turn a `BIN` (building identifier number, the DOB building indentifier) into a is-it-done-yet date
enables a whole range of things. See, for example, the [nyc-construction-timeline](https://github.com/ResidentMario/nyc-construction-timeline)
and [nyc-active-construction-sites](https://github.com/ResidentMario/nyc-active-construction-sites) repositories.

## Environment

You will need a `Python 2.7` environment booted up with the following libraries:

    pip install requests
    pip install bs4
    pip install selenium
    pip install arrow
    pip install tqdm
    pip install pdfminer
    conda install pandas
    conda install jupyter
    conda install seaborn

**You can install everything all at once using the packaged `environment.yml` by running `conda env create`**.

Notably, `pdfminer` (using the utility executable `pdf2txt.py`) is used to scrape text from the Certificate of
Occupacny PDFs using a command like the following one:

    pypdfocr marshalls_2012_record.pdf

(You do not need to do so yourself manually; this is just how, internally, `co_reader` operates.)

It is `pdfminer` which imposes the restriction that this environment by `Python 2.7`. It is the only library
 in this stack which, as of mid-2016, is still Python 2 only.

For more technical details, read the source code&mdash;it is well-documented and eminently readable.