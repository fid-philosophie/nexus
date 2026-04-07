""" module manages querying/requesting LOD sources and factlet creation """

import json
import requests
from jsonpath_ng import jsonpath
from jsonpath_ng.ext import parse
import time
from jsonschema import validate, ValidationError
from lxml import etree
import re
import pandas
import concurrent.futures
import argparse
import os

#import nexus_cache #!local module!

import hashlib
import redis
import requests

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0) # redis client

print("Redis ping:", r.ping()) # crash immediately if Redis unavailable

class Factlet:
    """ content + context """
    #
    # cf. https://graphentechnologien.hypotheses.org/files/2021/02/Thaller-Mainz2021-2.pdf
    # => "Tokens taken from sources are data. Provisionally interpreted they become information. A token together with the data needed for its interpretation is called a factlet." (p2)
    # => "Note: Tokens can be texts – and will be frequently so – are not required to be so." (p2)

    def __init__(self):
        _name = None                # the factlet's/field's name, try to make it self-explaining
        _description = None         # a short description
        _value = None               # the actual value/content
        _timestamp = None           # time of factlet creation
        _fuzzy_isA = None           # corresponding classes in different ontologies
        _subject = None             # entity that is described by the factlet (Wikidata- or GND-ID of described entity)
        _source_uri = None              # source of factlet => URI
        _source_name = None              # source of factlet => name
        _source_property = None     # specifies the corresponding property in source
        _source_date = None         # date of lastRevision or similar
        _source_path = None         # path in source to given data (XPATH/JSONPath/...)
        _source_licence = None      # licence for the data declared by the source
    
    # def __init__(self, value, timestamp, fuzzy_isA, subject, source, source_property, source_date, source_path, source_licence):
    #     self._value = value
    #     self._timestamp = timestamp
    #     self._fuzzy_isA = fuzzy_isA
    #     self._subject = subject
    #     self._source = source
    #     self._source_property = source_property
    #     self._source_date = source_date
    #     self._source_path = source_path
    #     self._source_licence = source_licence

    def set_name(self, name):
        self._name = name

    def get_name(self):
        return self._name
    
    def set_description(self, description):
        self._description = description

    def get_description(self):
        return self._description

    def set_value(self, value):
        self._value = value

    def get_value(self):
        return self._value

    def set_timestamp(self, timestamp):
        self._timestamp = timestamp

    def get_timestamp(self):
        return self._timestamp
    
    def set_fuzzy_isA(self, fuzzy_isA):
        self._fuzzy_isA = fuzzy_isA

    def get_fuzzy_isA(self):
        return self._fuzzy_isA
    
    def set_subject(self, subject):
        self._subject = subject

    def get_subject(self):
        return self._subject
    
    def set_source_uri(self, source_uri):
        self._source_uri = source_uri

    def get_source_uri(self):
        return self._source_uri
    
    def set_source_name(self, source_name):
        self._source_name = source_name

    def get_source_name(self):
        return self._source_name

    def set_source_property(self, source_property):
        self._source_property = source_property

    def get_source_property(self):
        return self._source_property

    def set_source_date(self, source_date):
        self._source_date = source_date

    def get_source_date(self):
        return self._source_date

    def set_source_path(self, source_path):
        self._source_path = source_path

    def get_source_path(self):
        return self._source_path
    
    def set_source_licence(self, source_licence):
        self._source_licence = source_licence

    def get_source_licence(self):
        return self._source_licence
    
    def get_as_dict(self):
        """ returns the whole factlet as a dictionary """
        factlet_dict = {'name': self._name,
                        'description': self._description,
                        'value': self._value,
                        'timestamp': self._timestamp,
                        'fuzzy_isA': self._fuzzy_isA,
                        'subject': self._subject,
                        'source_uri': self._source_uri,
                        'source_name': self._source_name,
                        'source_property': self._source_property,
                        'source_date': self._source_date,
                        'source_path': self._source_path
                        }
        return factlet_dict

class Nexus:
    """ able to aggregate linked data according to a mapping (cf. nexus_mapping_schema.json) """

    def __init__(self):
        self._wikidata_id = None
        self._data = None
        self._request_response = {}
        self._gnd_response = None
        self._gnd_id = None
        self._mappings = None
        self._mappings_schema = None
        self._mapping_profile = None
        self._fields = []
        self._sources = []
        self._source_ranking = []
        self._source_formats = {}
        self._source_prefixes = {}
        self._source_suffixes = {}
        self._identifiers = {}

    def data_fallback(self, field_object, source_ranking, current_source = 0):
        """ recursive iteration through source_ranking returns available field of highest priority """
        if current_source < len(source_ranking):
            try:
                found = None
                for s in field_object['fieldSources']:
                    if s['sourceName'] == source_ranking[current_source]:
                        found = s
                        break
                else:
                    # no fallback source left for this field
                    found = None

                if found is not None:
                    field_value = None
                    match self._source_formats[source_ranking[current_source]]:
                        case 'json':
                            if source_ranking[current_source] in self._request_response:
                                field_value = self.resolve_jsonpath(found['pathInSource'],self._request_response[source_ranking[current_source]]['response'],False)
                            else:
                                print(source_ranking[current_source] + ' without request response')
                                """ placeholder """
                        case 'xml':
                            if source_ranking[current_source] in self._request_response:
                                field_value = self.resolve_xpath(found['pathInSource'],self._request_response[source_ranking[current_source]]['response'],False)
                            else:
                                print(source_ranking[current_source] + ' without request response')
                                """ placeholder """
                        case _:
                            print('trying to resolve a path of a format (' + self._source_formats[source_ranking[current_source]] +') that is not supported')

                    if field_value is not None:
                        # found something in that field => create factlet:
                        new_factlet = Factlet()
                        new_factlet.set_name(field_object['fieldName'])
                        new_factlet.set_description('...')
                        new_factlet.set_value(field_value)
                        new_factlet.set_timestamp(time.time())
                        new_factlet.set_fuzzy_isA(found['fuzzyIsA'])
                        new_factlet.set_subject(self._identifiers)
                        new_factlet.set_source_uri(self._source_prefixes[source_ranking[current_source]] + self._identifiers[found['sourceName']] + self._source_suffixes[source_ranking[current_source]])
                        new_factlet.set_source_name(found['sourceName'])
                        new_factlet.set_source_date('')
                        new_factlet.set_source_path(found['pathInSource'])
                        new_factlet.set_source_property(found['property'])
                        new_factlet.set_source_licence('')
                        return new_factlet.get_as_dict()
                    else:
                        # fall back to next source
                        return self.data_fallback(field_object, source_ranking, current_source + 1)
                else:
                    # fall back to next source
                    return self.data_fallback(field_object, source_ranking, current_source + 1)
            except Exception as e: 
                print(f"Something went wrong: {e}")
                self.data_fallback(field_object, source_ranking, current_source + 1)
        else:
            # no fallback sources left
            return None

    def aggregate(self):
        """ aggregates the different sources according to nexus_mappings.json """
        fields = self.resolve_jsonpath('$.*[?(@.mappingProfile == "' + self._mapping_profile +'")].mappingFields', self._mappings)
        sources = self.resolve_jsonpath('$.*[?(@.mappingProfile == "' + self._mapping_profile +'")].mappingSources', self._mappings)

        sources = sorted(sources, key=lambda item: item['sourcePriority'], reverse=True) # sort list by sourcePriority (which is rated 0 to 100), descending

        # request sources in parallel (each source only once), responses will be stored in self._sources:
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for k, v in self._identifiers.items():
                for s in sources:
                    if s['sourceName'] == k:
                        futures.append(executor.submit(self.request, k, v))
                        break
            concurrent.futures.wait(futures)

            # communicate possible timeouts/fails:
            for fut in concurrent.futures.as_completed(futures):
                try:
                    _ = fut.result()
                except TimeoutError as e:
                    print(f"TIMEOUT: {e}")
                except Exception as e:
                    print(f"FAILED: {e}")

        # get data of fields according to priority/ranking of sources:            
        for field in fields:
            new_factlet = self.data_fallback(field, self._source_ranking, 0)
            if new_factlet is not None:
                self._fields.append(new_factlet)

    def set_identifier(self, source_name, identifier):
        self._identifiers[source_name] = identifier

    def get_identifier(self, source_name):
        return self._identifiers[source_name]

    def set_identifiers(self, dict_identifiers):
        self._identifiers = self._identifiers | dict_identifiers # merge dictionaries and update existing keys with dict_identifiers values

    def get_mapping_profile(self):
        return self._mapping_profile

    def get_request_response(self, source_name):
        return self._request_response[source_name]['response']
    
    def set_mappings_json(self, mappings_json, mappings_schema_json):
        self._mappings = mappings_json
        self._mappings_schema = mappings_schema_json

    def set_mapping_profile(self, mapping_profile):
        self._mapping_profile = mapping_profile

    def mappings_json_is_valid(self):
        """ validation of mapping_json """
        if self._mappings is not None and self._mappings_schema is not None:
            # validate mapping against its schema:
            try:
                validate(instance=self._mappings, schema=self._mappings_schema)
                return True
            except ValidationError as e:
                print(e.message)
                print('nexus_mappings_json is not valid')
                return False
        else:
            print('error: mappings not set')
            return False
    
    def load_sources(self):
        """ set up sources & their ranking/priorities from mapping """
        sources = self.resolve_jsonpath('$.*[?(@.mappingProfile == "' + self._mapping_profile +'")].mappingSources', self._mappings)
        sources = sorted(sources, key=lambda item: item['sourcePriority'], reverse=True) # sort list by sourcePriority (which is rated 0 to 100), descending
        for source in sources:
            self._source_ranking.append(source['sourceName'])
            self._source_formats[source['sourceName']] = source['sourceFormat']
            self._source_prefixes[source['sourceName']] = source['sourcePrefix']
            self._source_suffixes[source['sourceName']] = source['sourceSuffix']

    def resolve_xpath(self, find_xpath, in_source, first_only=True):
        """ resolve xpath and return first value """
        xpath_result = in_source.xpath(find_xpath)
        if len(xpath_result)>0:
            if first_only:
                xpath_result_return = str(xpath_result[0]) # get the very first value only
            else:
                xpath_result_return = str(xpath_result) # get all values
        else:
            xpath_result_return = None # ?
        return xpath_result_return

    def resolve_jsonpath(self, find_jsonpath, in_source, first_only=True):
        """ resolve jsonpath and return first value """
        jsonpath_result = parse(find_jsonpath).find(in_source)

        if len(jsonpath_result)>0:
            if first_only:
                jsonpath_result_return = jsonpath_result[0].value # get the very first value only
            else:
                values = [m.value for m in jsonpath_result] # get the actual values without the context
                jsonpath_result_return = values
        else:
            jsonpath_result_return = None # ?
        return jsonpath_result_return

    def request(self, source_name, source_item_id):
        """ make HTTP request for the nexus entity, store response in self._sources[] """

        # default User-Agent header (change accordingly):
        default_headers = {
            "User-Agent": "NexusAPI/1.0 (https://philportal.de/philfinder; nils.geissler@uni-koeln.de)"
        }
       
        source_prefix = self.resolve_jsonpath('$.*[?(@.mappingProfile == "' + self._mapping_profile +'")].mappingSources[?(@.sourceName == "' + source_name +'")].sourcePrefix', self._mappings)
        source_suffix = self.resolve_jsonpath('$.*[?(@.mappingProfile == "' + self._mapping_profile +'")].mappingSources[?(@.sourceName == "' + source_name +'")].sourceSuffix', self._mappings)
        source_format = self.resolve_jsonpath('$.*[?(@.mappingProfile == "' + self._mapping_profile +'")].mappingSources[?(@.sourceName == "' + source_name +'")].sourceFormat', self._mappings)
        source_headers = self.resolve_jsonpath('$.*[?(@.mappingProfile == "' + self._mapping_profile +'")].mappingSources[?(@.sourceName == "' + source_name +'")].sourceHeaders', self._mappings)

        parsed_headers = {}
        for h in source_headers:
            key, value = h.split(":", 1)
            parsed_headers[key.strip()] = value.strip()
        merged_headers = {**default_headers, **parsed_headers}

        url = source_prefix + str(source_item_id) + source_suffix # NOTE: this doesn't make sense as it is rn => IDs should also be dependent on mapping (of sources)...
        
        request_response = fetch_with_cache(url, merged_headers, ttl_seconds=3600)
        if request_response.status_code == 200:
            match self._source_formats[source_name]:
                case 'json':
                    self._request_response[source_name] = {'response': request_response.json(), 'format': source_format}
                case 'xml':
                    response_text = request_response.text
                    cleaned_text = response_text.replace('\n', '') # NOTE: might be only for VIAF...
                    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip() # NOTE: might be only for VIAF...
                    self._request_response[source_name] = {'response': etree.fromstring(cleaned_text), 'format': source_format}
                case _:
                    print('trying to convert a request response with a format (' + self._source_formats[source_name] +') that is not supported')
        else:
            print("HTTP request to " + source_name + " returned error: " + str(request_response.status_code))

    def get_aggregation(self, mappings_json, mappings_schema_json, mapping_profile, dict_identifiers):
        """ return aggregation of linked data (as factlets) """
        self.set_mappings_json(mappings_json, mappings_schema_json)
        self.set_mapping_profile(mapping_profile)
        self.set_identifiers(dict_identifiers)
        if self.mappings_json_is_valid():
            self.load_sources()
            self.aggregate()
            return self._fields
        
    def get_aggregation_flat(self, mappings_json, mappings_schema_json, mapping_profile, dict_identifiers):
        """ return a flat version of get_aggregate without context/provenance data """
        aggregated_fields = self.get_aggregation(mappings_json, mappings_schema_json, mapping_profile, dict_identifiers)
        aggregation_flat = {}
        for f in aggregated_fields:
            aggregation_flat[f['name']] = f['value']
        return aggregation_flat
    

    def get_aggregation_json(self, mappings_json, mappings_schema_json, mapping_profile, dict_identifiers):
        """ return a JSON version of get_aggregate """
        aggregated_fields = self.get_aggregation(mappings_json, mappings_schema_json, mapping_profile, dict_identifiers)
        #aggregation_json = json.dumps(aggregated_fields)
        aggregation_json = aggregated_fields
        return aggregation_json

def generate_nexus_mappings_json(mappings_dir: str = "mappings"):
    """ 
    - creates one large json file from the separate profiles (from folder 'mappings')
    - root json object is 'mappings' containing a list of profile objects 
    """
    all_mappings = []

    for filename in os.listdir(mappings_dir):
        if filename.endswith(".json"):
            filepath = os.path.join(mappings_dir, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    all_mappings.append(data)
                except json.JSONDecodeError as e:
                    print(f"⚠️ Skipping {filename}, invalid JSON: {e}")

    result = {"mappings": all_mappings}
    return result

class SimpleResponse:
    """Lightweight response-like object for cached + live responses."""
    def __init__(self, status_code: int, text: str, headers=None, url: str | None = None):
        self.status_code = status_code
        self.text = text
        self.headers = headers or {}
        self.url = url
        self.ok = 200 <= status_code < 400

    def json(self):
        return json.loads(self.text)

    def raise_for_status(self):
        if not self.ok:
            # Keep behavior close to requests
            raise requests.HTTPError(f"{self.status_code} Error for url: {self.url}", response=self)

def _cache_key(url: str, merged_headers: dict) -> str:
    key_raw = f"{url}|{tuple(sorted(merged_headers.items()))}"
    return "httpcache:" + hashlib.sha256(key_raw.encode("utf-8")).hexdigest()

def fetch_with_cache(url: str, merged_headers: dict, ttl_seconds: int = 3600) -> SimpleResponse:
    """
    Fetch URL with caching in Redis.
    - Key: SHA256(url + sorted(headers))
    - Cached value: JSON envelope {status, text, headers, url}
    - Returns: SimpleResponse with .status_code, .text, .json(), .headers, .url
    """
    cache_key = _cache_key(url, merged_headers)

    # Try cache
    cached = r.get(cache_key)
    if cached:
        print("CACHE HIT") # debugging caching
        print(cache_key) # debugging caching
        env = json.loads(cached)
        # Mark cache hit in headers (optional)
        env_headers = env.get("headers") or {}
        env_headers.setdefault("X-Cache", "HIT")
        return SimpleResponse(env["status"], env["text"], env_headers, env.get("url"))

    # Fetch live
    req = requests.get(url, headers=merged_headers, timeout=10)
    env = {
        "status": req.status_code,
        "text": req.text,
        "headers": dict(req.headers),
        "url": req.url,
    }

    # Cache only successful responses (200). Adjust if you want other codes cached.
    if req.status_code == 200:
        r.setex(cache_key, ttl_seconds, json.dumps(env))

    # Return a SimpleResponse for consistent interface
    return SimpleResponse(env["status"], env["text"], env["headers"], env["url"])

def load_mappings(nexus_mappings_json: str):
    """  check if a custom mapping was given or the default mappings should be used """
    if nexus_mappings_json == "default":
        # Load from the default files
        return generate_nexus_mappings_json()
    else:
        with open(nexus_mappings_json, 'r', encoding='utf-8') as file:
            print("opened " + nexus_mappings_json + "...")
            return json.load(file)

def wikidata_to_authorities(dict_identifiers):
    """ should be triggered if only Wikidata identifier was given => try to get data from all available sources"""
    with open('nexus_mappings_schema.json', 'r', encoding='utf-8') as file:
        nexus_mappings_schema_json = json.load(file)
    nexus_mappings_json = generate_nexus_mappings_json()
    interim_nexus = Nexus()
    interim_aggregation = interim_nexus.get_aggregation_flat(nexus_mappings_json, nexus_mappings_schema_json, "hub_wikidata", dict_identifiers)
    return interim_aggregation

def run_nexus(given_mapping_profile, given_dict_identifiers, given_add_identifiers, given_flatten, given_nexus_mappings_json: str = "default"):
    """ encapsulated 'main' """
    dict_identifiers = json.loads(given_dict_identifiers.replace("'", '"'))
    # if more_ids flag is true and a Wikidata identifier was given, try to get identifiers for other sources
    # warning: this will overwrite any other identifer than Wikidata!
    if given_add_identifiers == True:
        if "Wikidata" in dict_identifiers:
            print("fetching additional identifiers via wikidata_to_authorities...")
            all_identifiers = wikidata_to_authorities({"Wikidata": dict_identifiers["Wikidata"]})
            # output values come nested in an array => flatten it to conform the input format:
            all_identifiers = {k: v[0] if isinstance(v, list) and len(v) == 1 else v
                        for k, v in all_identifiers.items()}
        else:
            all_identifiers = dict_identifiers
    else:
        all_identifiers = dict_identifiers

    my_nexus = Nexus()
    with open('nexus_mappings_schema.json', 'r', encoding='utf-8') as file:
        nexus_mappings_schema_json = json.load(file)
    if given_nexus_mappings_json == "default":
        nexus_mappings_json = generate_nexus_mappings_json()
    else:
        with open(given_nexus_mappings_json, 'r', encoding='utf-8') as file:
            print("opened " + given_nexus_mappings_json + "...")
            nexus_mappings_json = json.load(file)



    if given_flatten == True:
        my_nexus_aggregation_json = my_nexus.get_aggregation_flat(nexus_mappings_json, nexus_mappings_schema_json, given_mapping_profile, all_identifiers)
    else:
        my_nexus_aggregation_json = my_nexus.get_aggregation_json(nexus_mappings_json, nexus_mappings_schema_json, given_mapping_profile, all_identifiers)
    return my_nexus_aggregation_json

def main():
    p = argparse.ArgumentParser()
    p.add_argument("nexus_mappings_json", type=str, help="a mapping that conforms to the schema defined in nexus_mappings_schema.json, use 'default'", default="default")
    p.add_argument("mapping_profile", type=str, help="one of the profiles provided in your nexus_mappings_json, 'default' mapping contains profiles 'person' and 'work'")
    p.add_argument("dict_identifiers", type=str, help="a (stringified) dictionary of identifiers (e.g. {'Wikidata': 'Q9312', 'GND': '118559796', 'LCNAF': 'n79021614', 'VIAF': '82088490'} for Immanuel Kant)")
    p.add_argument("add_identifiers", type=bool, help="", default=True)
    p.add_argument("flatten", type=bool, help="", default=True)
    args = p.parse_args()

    if not args.nexus_mappings_json:
        print("Error: no input nexus_mappings_json specified")
    if not args.mapping_profile:
        print("Error: no input mapping_profile specified")
    if not args.dict_identifiers:
        print("Error: no input dict_identifiers specified")

    jsondumps = json.dumps(run_nexus(args.mapping_profile, args.dict_identifiers, args.add_identifiers, args.flatten, args.nexus_mappings_json), ensure_ascii=False, indent=4)
    if(jsondumps=="[]"):
        print("aggregation returned no data")
    else:
        print(jsondumps)
        

if __name__ == "__main__":
    main()
