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

    pdf2txt marshalls_2012_record.pdf

(You do not need to do so yourself manually; this is just how, internally, `co_reader` operates.)

It is `pdfminer` which imposes the restriction that this environment by `Python 2.7`. It is the only library
 in this stack which, as of mid-2016, is still Python 2 only.

For more technical details, read the source code&mdash;it is well-documented and eminently readable.

## Capacities

At the moment this module is meant for text extraction of C of O issuance dates.

However, you can extend it yourself so that it extracts any (machine-readable) text feature from a (recent) C of O by replacing `_harvest_certificate_date_from_pdf` (which does the actual text mining and date extraction) with your own "reducer" function. 

Examples of other extractable features: unit count; certificate type; applicable building code; number of stories; etc.

## Limitations

This module uses a simple text extraction facility to do its work, so it relies on the certificate of occupancy being uploaded in a machine-readable (2003+) and unencrypted (also 2003+?) format.

Older documents (going back to circa 1916) are available in a combination of handwritten/typed formats, for obvious reasons, and strangely they are all encrypted as well, making reading them impossible. You can get around this by running optical character recognition on them first and extracting the text from the scanned copy. A stub method for doing so, using `pyocr`, exists in the source code, but is not currently implemented.

C of Os filed within the last ten years (or so) are all uploaded using [the same machine readable format](https://github.com/ResidentMario/nyc-certificates-of-occupancy/blob/master/2015%20Example.pdf). C of Os dating from about 2003 are also machine readable, but have an older format. Forms older than 2002 or so are not machine readable, but I believe are high enough quality to submit to optical character recognition well. The scan quality gets iffier and iffier the further back you go; I would say, don't expect to get anything out of documents older than about the mid-1990s. You can see this for yourself in my [example gallery repo](https://github.com/ResidentMario/nyc-certificates-of-occupancy)).
