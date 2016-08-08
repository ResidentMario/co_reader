#!python2.7

"""
This module implements a Certificate of Occupancy reader, which, given a building's BIN, returns the date of the most
recent Occupancy certificate issued for the BIN.
"""


from __future__ import print_function
import requests
import bs4
import subprocess
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import arrow
import time
import string

__author__ = "Aleksey Bilogur"
__email__ = "aleksey@residentmar.io"


_driver = webdriver.PhantomJS()


def _get_certificate_pdf_links(bin):
    """
    Given a BIN, returns the name of the PDF of the corresponding with the CO associated with that BIN.
    This data is taken from the NYC Department of Buildings (DOB) Building Information System (BIS),
    a web application hooked up into the DOB master building mainframe that first went live in 2001. The BIS allows
    one to look up all of the information DOB has on the building in question by address or BIN; information
    includes size, construction, permits, violations, fines, and so on.
    Since the URL which encodes this information is attached to a BIN, we can quickly locate the BIS page for a
    building by its BIN. The "List Certificates of Occupation" page, attached to this page by a link, is similarly
    easy to access.
    The trouble is that the application is rather old and cranky, so access to it is regulated by a load balancing
    access pane which prints a webpage telling you you're going to have to wait a bit when load is high. A simple
    web scraper (e.g. requests) would scrape that load-balancing page and report back a failure, which we don't
    want (if you want to see the wait screen yourself I saved a screenshot of it at wait_screen.png, have a gander).
    I used the Python binding of selenium to get around this. Selenium is a full-fledged browser virtualizer that
    has a lot of additional capacities---the one we're using here is the ability to wait until the page reloads
    and the loading pane is gone.
    Note that the selenium instance used here requires PhantomJS to work. PhantomJS is a so-called "headless
    browser" which is like an ordinary browser like Firefox, except it doesn't bother displaying the pages,
    allowing it to go through page scrapes (as here) more efficiency.
    Once we have the page HTML I scape that using BeautifulSoup to get the PDF link.
    """
    req_str = "http://a810-bisweb.nyc.gov/bisweb/COsByLocationServlet?requestid=&allbin={0}".format(bin)
    _driver.get(req_str)
    print("Requested BIN {0} data from BIS, awaiting response...".format(bin))
    try:
        webdriver.support.ui.WebDriverWait(_driver, 10).until(
            EC.title_is("Property Overview")
        )
    finally:
        print("Got a response.")
        raw_html = _driver.find_element_by_tag_name("body").get_attribute('innerHTML')
        dom = bs4.BeautifulSoup(raw_html, 'html.parser')
        return [str(link.text) for link in dom.select("a[href]") if "PDF" in link.text or "pdf" in link.text]
    # The following code is a minimum working example of selenium in action:
    # browser = webdriver.PhantomJS()
    # print(browser)
    # browser.get('http://seleniumhq.org/')
    # browser.save_screenshot('screen.png')
    # The follow code is a working simpler implementation of the above using requests but not accounting for the wait:
    # req_str = "http://a810-bisweb.nyc.gov/bisweb/COsByLocationServlet?requestid=&allbin={0}".format(bin)
    # dom = bs4.BeautifulSoup(requests.get(req_str).text, 'html.parser')
    # return [link.text for link in dom.select("a[href]") if "PDF" in link.text or "pdf" in link.text]


def _download_certificate_pdf(co_link, borough_code):
    """
    Given the filename of the PDF for the C of O of a building, as per _get_co_pdf_links(), and the borough code (as
    per the permit data), downloads that PDF.
    The URL signature required for accessing the C of O PDF is very complex, and required a lot of analysis to
    figure out. Here's an example URL:
    http://a810-bisweb.nyc.gov/bisweb/CofoDocumentContentServlet?passjobnumber=null&cofomatadata1=cofo
    \&cofomatadata2=M&cofomatadata3=000&cofomatadata4=092000&cofomatadata5=M000092531.PDF&requestid=5
    For reference "M000092531.PDF" is the root filename in this case.
    Each of the parameters must be filled in (otherwise you will receive a silent 404 page):
    passjobnumber=null      --- Can be left as null. Doesn't seem to have an effect?
    cofomatdata1=cofo       --- Must be cofo, whatever that is.
    cofomatadata2=?         --- Must be the borough code. Borough codes are a semi-standard lexicon for referring to
                                boroughs; the key is below. Note that two-letter codes (used in PLUTO) andd borough
                                numbers (used in PAD) are also common ids.
    cofomatadata3=###       --- Must be the first three numerical digits of the filename (why? dunno).
    cofomatadata4=######    --- Must be the last three numerical digits of the filename (why? dunno).
    cofomatadata5=[variable length].pdf
                            --- The full filename, as given on the landing page for the BIN.
    requestid=5             --- This parameter doesn't seem to matter. Perhaps randomizing this will reduce the rate
                                limit?
    Here are the borough codes:
    B --- Brooklyn
    Q --- Queens
    M --- Manhattan
    R --- Staten Island
    X --- The Bronx
    What are these mysterious filenames? Heavens knows; obviously they have some regularities but mostly they tend
    towards chaos. But the filename encoding does have some sort of pattern:
    1290125.PDF             --- Just a bunch of numbers. The first digit tends to be the borough number.
    M1912571.PDF            --- A bunch of numbers prepended by a single letter for the borough code.
    1210125-2.PDF           --- A bunch of numbers, a dash, one more number. Usually from follow-up permits.
    M1208518-3.PDF          --- Por que no los dos?
    Note that Selenium, the Python library I used to wait through the loading pane in the above method,
    chokes on PDF waiting, something I didn't know ahead of time. So this method uses the fallback method of sending a
    normal request, verifying that the content received is PDF, and then resending the request five seconds later if
    it is not. However, whilst technically challenging, it may nevertheless be possible:
    http://stackoverflow.com/questions/37953182/how-do-i-wait-through-a-wait-page-and-then-download-a-pdf-using
     -python/37954928#37954928
    This method returns an error code: True if it ran successfully, False if not.
    """
    if co_link[0] in string.ascii_uppercase:
        co_link_shortened = co_link[1:]
    else:
        co_link_shortened = co_link
    req_str = "http://a810-bisweb.nyc.gov/bisweb/CofoDocumentContentServlet?passjobnumber=null&cofomatadata1=cofo" \
          u"&cofomatadata2={0}&cofomatadata3={1}&cofomatadata4={2}&cofomatadata5={3}&requestid=5".format(
        borough_code, co_link_shortened[0:3], co_link_shortened[3:6] + "000", co_link)
    r = requests.get(req_str)
    # If we get the PDF immediately we are done.
    if r.headers['content-type'] == "application/pdf":
        print("PDF Certificate of Occupancy '{0}' retrieved.".format(co_link))
        with open('temp.pdf', 'wb') as f:
            for chunk in r.iter_content(2000):
                f.write(chunk)
        return True
    # If we do not get the PDF immediately we either get a silent 404 page or an error message.
    # First we respond to the case of a 404. This is really bad because it means our encoding scheme is wrong!
    elif "java.io.FileNotFoundException" in r.text[:500]:
        print("Error attempting to retrieve PDF Certificate of Occupancy '{0}'!".format(co_link))
        print("This is a serious but non-fatal error indicating an error in our filename reverse engineering.")
        return False
    # Otherwise we have hit a waiting screen. So we will resend queries every five seconds until we get it.
    else:
        while "waiting-main" in r.text[:500]:
            print("Got the wait page. Trying to retrieve the PDF Certificate of Occupancy '{0}' again in five "
                  "seconds...".format(co_link))
            time.sleep(5)
            r = requests.get(req_str)
        print("After some delay, PDF Certificate of Occupancy '{0}' retrieved.".format(co_link))
        with open('temp.pdf', 'wb') as f:
            for chunk in r.iter_content(2000):
                f.write(chunk)
        return True


def _copy_pdf_using_ocr(pdf_filename):
    """
    Given the freshly-downloaded PDF document containing the CO, uses optical character recognition to convert the
    file to a readable format.
    The direct approach, and the one I expected would work, is reading the file in, getting a text dump of it,
    and then extracting the application date from there. However, to my immense surprise these files are locked and
    password-encrypted. Really! You're serious! Well, so much for public goods.
    Ok, plan B: convert the PDF to an image and do a screen capture. I use pypdfocr for this.  Amazingly enough the
    end result is an exact copy of the original PDF! So all that encryption achieved was adding five seconds or so
    to processing time. Bleh.
    This method returns the filename of the freshly converted PDF.
    """
    subprocess.Popen("pypdfocr {0}".format(pdf_filename), shell=True)
    return pdf_filename.replace(".pdf", "_ocr.pdf")


def _harvest_certificate_date_from_pdf(ocr_pdf_link):
    """
    Given the freshly-downloaded PDF document containing the CO, attempts to return the CO approval date.
    Uses the pdf2txt utility command (from pdfminer) to convert to text. A simple regex extracts a list of all of
    the dates, from whence we get the minimum date and return it as a datetime object.
    Note that this scrape will completely fail on the older poorly scanned forms. But recent documents (2001?+) are
    readable and should work; the recent ones (for the purposes of which this script was written) will work for sure.
    """
    p = subprocess.Popen(["pdf2txt.py", ocr_pdf_link], stdout=subprocess.PIPE)
    output = p.communicate()[0]
    # Dates must be of the form "12/24/2012" to get read at this juncture.
    date_strs = re.findall("[0-9]{2}[/][0-9]{2}[/][0-9]{4}", output)
    print(date_strs)
    if date_strs:
        # The following expression collects dates, converts them to Arrow objects, find the minimum date,
        # and then posts the datetime version of the minimum date (e.g. converts the final arrow object into a
        # datetime one).
        # New-style forms all use this date format. Old-style and derivative date formats we will not attempt to read.
        try:
            return min([arrow.get(date_str, 'MM/DD/YYYY') for date_str in date_strs]).datetime
        except ValueError:
            return
    else:
        return


def get_co_date(bin, borough_code):
    """
    Given a BIN, returns the date of the most recent CO filed for the building corresponding with that BIN.
    A "certificate of occupancy" (C-of-O or CO) is a legal document in New York City indicating that a property is
    legally certified for occupancy.
    Such a document must be obtained every time significant construction is done on a building---this appears to
    mean construction of a new building, modifications to a building resulting in a change of egress (entrance and
    exit), or a substantial change in the use of the building.
    This does NOT include things like simple or even somewhat substantial renovations---of the three classes of
    renovations recognized by the Department of Buildings, classes I II and III, only class I renovations require
    the issuance of a new CO, corresponding with a major re-purposing of the building.
    From our limited observations a CO does not appear to be a particularly fine-grained entity. So converting a
    warehouse to a hipster residential apartment complex would necessitate a CFO. Opening a new restaurant where an
    old one was does not. Nor would opening that restaurant where a pharmacy used to be. Opening a gas station?
    Probably. Something in between? Unclear...
    A "building identification number" (BIN) is a number that is assigned by DOF, DOB, DCAS, and a few other
    entities in some fairly convoluted manner to each individual building licensed and tracked by New York City. For
    more on BINs read the PDF in the "BIN Working Group" file in our directory.
    """
    pdf_links = _get_certificate_pdf_links(bin)
    min_certs = []
    print("Discovered {0} Certificates of Occupancy.".format(len(pdf_links)))
    for pdf_link in pdf_links:
        print("Scanning {0}...".format(pdf_link))
        success_status = _download_certificate_pdf(pdf_link, borough_code)
        # If the download returns False, indicating a failure, just skip to the next document in the loop.
        if not success_status:
            continue
        # If the download returns True, run the resultant PDF through the scrape.
        print("Copying text using optical character recognition...")
        # temp_ocr = _copy_pdf_using_ocr("temp.pdf")
        print("Harvesting dates...")
        # co = _harvest_certificate_date_from_pdf(temp_ocr)
        try:
            co = _harvest_certificate_date_from_pdf("temp.pdf")
        except:
            print("Date harvesting failed! Probably the PDF was edit-locked. Skipped, for now.")
            co = None
        if co:
            print("Date(s) found!")
            min_certs.append(co)
        else:
            print("No date found. Continuing...")
        # break
    # Return the maximum recognized minimum certificate obtained if dates are found, None otherwise.
    if min_certs:
        return max(min_certs)
    else:
        return None