#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    Define global (to icoscp) common tool to search for
    country information based on a static local file
    country.json  -> credit to https://github.com/mledoze/countries
    and for reverse geocoding -> credit to
    https://nominatim.openstreetmap.org
"""

import importlib.resources as pkgres
import json
import requests
import icoscp


class UnableToGeocode(Exception):
    pass


def get(**kwargs):
    """
    Search country information.
    Please note: in case you provide more than one parameter, the order
    of keywords is not respected. The execution order is always like
    the function signature and as soon as a result is found, it will be
    returned and the search is stopped.

    Accepted keywords: code='', name='', latlon=[], search=''

    Example:
        .get()                      list of dict: all countries
        .get(code='CH')             dict: Switzerland
        .get(name='greece')         dict: Greece
        .get(latlon=[48.85, 2.35])  dict:
        .get(search='europe')

    Parameters
    ----------
    code : STR
        Search by ISO 3166-1 2-letter or 3-letter country codes

    name : STR
        search by country name, including alternativ spellings.
        It can be the native name or a partial name.

    latlon : List[]
        List with two integer or floating point numbers representing
        latitude and longitude. BE AWARE: using an external service
        from openstreetmap for reverse geocoding

    search : STR
        arbitrary text search, not case sensitiv, search in all fields

    Returns
    -------
    DICT: if a single country is found
    LIST[DICT]: list of dicts if more than one countre
    BOOL (False) if no result

    """

    # create a ressource file and read
    countries = pkgres.read_text(icoscp, 'countries.json')
    countries  = json.loads(countries)

    if not kwargs:
        return countries

    if 'code' in kwargs.keys():
        return _c_code(kwargs['code'], countries)


    if 'name' in kwargs.keys():
        return _c_name(kwargs['name'], countries)

    if 'search' in kwargs.keys():
        return _c_search(kwargs['search'], countries)

    if 'latlon' in kwargs.keys():
        latlon = kwargs['latlon']
        if isinstance(latlon, list) and len(latlon) == 2:
            country = _c_reverse(latlon)
        if country:
            return _c_code(country, countries)

    return False

def _c_search(search, countries):
    country = []
    for ctn in countries:
        if search.lower() in str(ctn).lower():
            country.append(ctn)

    if not country:
        return False

    if len(country) ==1 :
        #return the dictionary rather than the list
        return country[0]

    return country


def _c_code(code, countries):
    country = []
    for ctn in countries:
        if code.lower() == str(ctn['cca2']).lower() or \
            code.lower() == str(ctn['cca3']).lower():

            country.append(ctn)
    if not country:
        return False

    if len(country) ==1 :
        #return the dictionary rather than the list
        return country[0]

    return country

def _c_name(name, countries):
    country = []
    for ctn in countries:
        if name.lower() in str(ctn['name']).lower() \
             or name.lower() in str(ctn['altSpellings']).lower():

            country.append(ctn)


    if not country:
        return False

    if len(country) ==1 :
        #return the dictionary rather than the list
        return country[0]

    return country


def _c_reverse(latlon):
    # Icos nominatim service is the first responder to a reverse
    # geocoding request.
    icos_base = 'https://nominatim.icos-cp.eu/reverse?format=json&'
    icos_url = icos_base + 'lat=' + str(latlon[0]) + '&lon=' + str(latlon[1]) + '&zoom=3'
    zoom_3 = True
    try:
        icos_response = requests.get(url=icos_url)
        json_content = icos_response.json()
        if icos_response.status_code == 200:
            if 'error' not in json_content.keys() and 'address' in json_content.keys():
                return json_content['address']['country_code']
            else:
                zoom_3 = False
        else:
            raise requests.exceptions.RequestException
    # If icos nominatim is unavailable try OpenStreetMap nominatim
    # service instead.
    except requests.exceptions.RequestException as request_exception:
        print('Request failed with: ' + str(request_exception))
        icos_info_message = 'Icos reverse geocoding service is unavailable.\n' \
                            'Redirecting to external https://nominatim.openstreetmap.org ...\n'
        print(icos_info_message)
    # todo: zoom 5 or no zoom at all?
    # Handle errors due to incomplete nominatim database.
    # Icos nominatim might be able to reverse geocode without
    # using zoom option.
    if not zoom_3:
        icos_url = icos_base + 'lat=' + str(latlon[0]) + '&lon=' + str(latlon[1])
        try:
            icos_response = requests.get(url=icos_url)
            json_content = icos_response.json()
            if icos_response.status_code == 200:
                if 'error' not in json_content.keys() and 'address' in json_content.keys():
                    return json_content['address']['country_code']
                else:
                    raise requests.exceptions.RequestException
            else:
                raise requests.exceptions.RequestException
        except requests.exceptions.RequestException as request_exception:
            print('Request failed: ' + str(request_exception))
            icos_info_message = 'Icos nominatim was unable to reverse geocode or less likely ' \
                                'the service crashed during two consequential requests.\n' \
                                'Redirecting to external OpenStreetMap nominatim ' \
                                'https://nominatim.openstreetmap.org ...\n'
            print(icos_info_message)
    # If icos nominatim is unavailable try OpenStreetMap nominatim
    # service instead.
    external_base = 'https://nominatim.openstreetmap.org/reverse?format=json&'
    external_url = external_base + 'lat=' + str(latlon[0]) + '&lon=' + str(latlon[1]) + '&zoom=3'
    try:
        external_response = requests.get(url=external_url)
        if external_response.status_code == 200:
            country = external_response.json()
            if 'address' in country.keys():
                return country['address']['country_code']
    except requests.exceptions.RequestException as e:
        print('Request failed with: ' + str(e))
        external_info_message = 'External geocoding services at ' \
                                'https://nominatim.openstreetmap.org are unavailable.\n'
        print(external_info_message)
    return False


if __name__ == "__main__":

    MSG = """

    # find country information from a static file with the icoscp library.
    # you can import this file with:

    from icoscp import country

    # arbitrary text search
    a = get(search='Europe')

    # search by country code (alpha2 & alpha3)
    b = get(code='SE')      # returns Sweden
    c = get(code='CHE')     # returns Switzerland

    # search by name, includes alternative spellings
    d = get(name = 'greece') # returns Greece
    e = get(name = 'helle' ) # returns Greece and Seychelles

    # search by lat lon...!! BE AWARE this is using an external
    # rest API from OpenStreeMap https://nominatim.openstreetmap.org
    f = get(latlon=[42.5,13.8]) # returns Italy
    """
    print(MSG)
