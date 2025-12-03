Maricopa County Assessor’s Office
API Documentation
Headers
Once you receive your token, the next step is to add a custom header to your request (documentation
varies between languages and transports). We use a custom header name of AUTHORIZATION with
a value of your token and user-agent with a value of null. Listed below are some links to various
examples of tools that are commonly used to access a RESTful API.
cURL (PHP/Command Line): https://curl.haxx.se/libcurl/c/CURLOPT_HTTPHEADER.html
GuzzleHTTP (PHP): http://docs.guzzlephp.org/en/stable/request-options.html
node.js (using Request): https://github.com/request/request
C#/ASP.NET/ASP.NET Core: https://docs.microsoft.com/en-
us/dotnet/api/system.net.webrequest.headers?view=netframework-
4.7.1#System_Net_WebRequest_Headers
If you need a token please use the contact us form in the upper right hand corner of the website and
select the option “API Question/Token.”
Description Of Usual Server Responses:
• 200 OK - the request was successful (some API calls may return 201 instead).
• 201 Created - the request was successful and a resource was created.
• 204 No Content - the request was successful but there is no representation to return (i.e. the response
is empty).
• 400 Bad Request - the request could not be understood or was missing required parameters.
• 401 Unauthorized - authentication failed or user doesn't have permissions for requested operation.
• 403 Forbidden - access denied.404 Not Found - resource was not found.
• 405 Method Not Allowed - requested method is not supported for resource.

Search Functions
Parameters
{query}
URL encoded query to search for
Search Property
Description: Searches all data points available. Returns a structured JSON result set with Real
Property, BPP, MH, Rentals, Subdivisions, and Content along with totals found.
Path: /search/property/?q={query}
Example: https://mcassessor.maricopa.gov/search/property/?q={query}
Paging within property results
Results are returned at 25 results at a time. To access results after 25 simply add the page number.
For example, if there are 250 results and you want to access results 201-225, then that would be
page 9.
Path: /search/property/?q={query}&page={number}
Example: https://mcassessor.maricopa.gov/search/property/?q={query}&page=9
Search Subdivisions
Description: Searches only subdivision names. Returns a structured JSON result set with a list of
subdivision names and parcel counts.
Path: /search/sub/?q={query}
Example: https://mcassessor.maricopa.gov/search/sub/?q={query}
Search Rentals
Description: Searches only rental registrations. Returns a structured JSON result set with only rental
registrations.
Path: /search/rental/?q={query}
Example: https://mcassessor.maricopa.gov/search/rental/?q={query}
Paging within rental results
Results are returned at 25 results at a time. To access results after 25 simply add the page number.
For example, if there are 250 results and you want to access results 201-225, then that would be
page 9.
Path: /search/ rentals /?q={query}&page={number}
Example: https://mcassessor.maricopa.gov/search/ rentals /?q={query}&page=9
Parcel Functions
Parameters
{apn}
APN (Assessor Parcel Number or APN for short) must formatted with (or without) spaces, dashes, or
dots.
Parcel Details
Description: Returns a JSON object with all available parcel data.
Works with parcel type(s): Residential, Commercial, Land, Agriculture
Path: /parcel/{apn}
Example: https://mcassessor.maricopa.gov/parcel/{apn}
Property Information
Description: Returns a JSON object with information specific to the property.
Works with parcel type(s): Residential, Commercial, Land, Agriculture
Path: /parcel/{apn}/propertyinfo
Example: https://mcassessor.maricopa.gov/parcel/{apn}/propertyinfo
Property Address
Description: Returns a JSON object with address of the property.
Works with parcel type(s): Residential, Commercial, Land, Agriculture
Path: /parcel/{apn}/address
Example: https://mcassessor.maricopa.gov/parcel/{apn}/address
Valuation Details
Description: Returns a JSON object with the past 5 years of valuation data from a parcel.
Works with parcel type(s): Residential, Commercial, Land, Agriculture
Path: /parcel/{apn}/valuations
Example: https://mcassessor.maricopa.gov/parcel/{apn}/valuations
Residential Details
Description: Returns a JSON object with all the available residential parcel data. Does not apply to
commerical, land or agriculture parcels.
Works with parcel type(s): Residential, Commercial, Land
Path: /parcel/{apn}
Example: https://mcassessor.maricopa.gov/parcel/{apn}/residential-details
Owner Details
Description: Returns a JSON object with all available parcel data.
Works with parcel type(s): Residential, Commercial, Land, Agriculture
Path: /parcel/{apn}/owner-details
Example: https://mcassessor.maricopa.gov/parcel/{apn}/owner-details
MCR
Description: Returns a JSON object ...
Works with parcel type(s): Residential, Commercial, Land, Agriculture
Path: /parcel/mcr/{mcr}
Example: https://mcassessor.maricopa.gov/parcel/mcr/{mcr}
Paging within rental results
Results are returned at 25 results at a time. To access results after 25 simply add the page number.
For example, if there are 250 results and you want to access results 201-225, then that would be
page 9.
Path: /parcel/mcr/{mcr}/?page={number}
Example: https://mcassessor.maricopa.gov/parcel/mcr/{mcr}/?page=9
Section/Township/Range (STR)
Description: Returns a JSON object ...
Works with parcel type(s): Residential, Commercial, Land, Agriculture
Path: /parcel/str/{str}
Example: https://mcassessor.maricopa.gov/parcel/str/{str}
Paging within rental results
Results are returned at 25 results at a time. To access results after 25 simply add the page number.
For example, if there are 250 results and you want to access results 201-225, then that would be
page 9.
Path: /parcel/str/{str}/?page={number}
Example: https://mcassessor.maricopa.gov/parcel/str/{str}/?page=9
MapID (Map Ferret/Plat Map)
Functions
Parameters:
{apn}
APN (Assessor Parcel Number or APN for short) must formatted with (or without) spaces, dashes, or
dots.
{mcr}
MCR Number.
{sub}
Subdivision name. Must be URL encoded.
{str}
Section/Township/Range. Can be formatted with dashes only.
{book}
Three digit book portion of an APN.
{map}
Two digit map portion of an APN.
Parcel Map(s)
Description: Returns a JSON array of map file names.
Path: /mapid/parcel/{apn}
Example: https://mcassessor.maricopa.gov/mapid/parcel/{apn}
Book/Map Map(s)
Description: Returns a JSON array of map file names.
Path: /mapid/bookmap/{book}/{map}
Example: https://mcassessor.maricopa.gov/mapid/bookmap/{book}/{map}
MCR Map(s)
Description: Returns a JSON array of map file names.
Path: /mapid/mcr/{mcr}
Example: https://mcassessor.maricopa.gov/mapid/mcr/{mcr}
Business Personal Property/Mobile
Home Functions
Parameters:
{acct}
Business personal property account number.
{type}
Business personal property account type character. Must be lower case and must be a single letter of
either 'c' for Commercial, 'm' for Multiple or 'l' for Lessor
{year}
Four digit tax year. Defaults to current tax year if omitted.
BPP Account(s) Details
Description: Returns either account details for a single, commercial account or account details
belonging to a multiple or lessor account. Optionally supply a tax year to get a list of accounts for that
tax year. Tax year does not apply to commercial accounts.
Path: /bpp/{type}/{acct}[/{year}]
Example: https://mcassessor.maricopa.gov/bpp/{type}/{acct}
Example: https://mcassessor.maricopa.gov/bpp/{type}/{acct}/{year}
Mobile Home Account
Description: Returns account details for an unsecured mobile home.
Path: /mh/{acct}
Example: https://mcassessor.maricopa.gov/mh/{acct}
Mobile Home VIN
Description: Returns account number on a mobile home VIN.
Path: /mh/vin/{vin}
Example: https://mcassessor.maricopa.gov/mh/vin/{vin}
Document updated February 1, 2024