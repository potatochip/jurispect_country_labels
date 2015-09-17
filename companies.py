from cleanco import cleanco
from textual import simple_match, fuzzy_match, process_string
import pandas as pd


df = pd.read_pickle('companies_venture.pkl')
comps = df[df.primary_role == 'company'][['name', 'location_city', 'location_region', 'location_country_code']]
clean_names = comps.name.dropna().map(process_string)
# clean_names = comps.name.dropna().map(clean_company_name) # way slow. will need to rewrite it.


def clean_company_name(s):
    s = process_string(s)
    cleaned = cleanco(s)
    return cleaned.clean_name()


def get_country_from_company_name(s):
    cleaned = cleanco(s)
    return cleaned.country()


def match_company(s1, s2):
    # strip company name of extraneous space and legal terms / abbreviations
    clean1 = clean_company_name(s1)
    clean2 = clean_company_name(s2)

    # only tries a fuzzy match if the clean version is identical
    if clean_company_name(s1) == clean_company_name(s2):
        return fuzzy_match(s1, s2)

    return False


def is_company(term):
    term = process_string(term)
    for company in clean_names:
        # if fuzzy_match(term, company, 0.9):
        if simple_match(term, company):
            print company
            # breaks and returns True first time it gets a match
            return True


def find_companies(entity_list):
    # entity_list = map(process_string, entity_list)
    return filter(is_company, entity_list)
