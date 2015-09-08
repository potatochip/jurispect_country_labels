'''
grabs countries from entities and raw text contextual clues
'''

import pandas as pd
from multiprocessing import Pool
from unidecode import unidecode
import pycountry
import jellyfish
import difflib
import csv
from collections import Counter
import re
import nltk
from nltk import bigrams
from nltk import trigrams


def standardize_country_name(name):
    try:
        name = unicode(name, 'utf8')
    except:
        pass
    name = correct_country_mispelling(name)
    return name


def title_except(s, exceptions=['a', 'an', 'of', 'the', 'is']):
    word_list = re.split(' ', s)       #re.split behaves as expected
    final = [word_list[0].capitalize()]
    for word in word_list[1:]:
        final.append(word in exceptions and word or word.capitalize())
    return " ".join(final)


def correct_country_mispelling(s):
    with open("ISO3166ErrorDictionary.csv", "rb") as info:
        reader = csv.reader(info)
        for row in reader:
            if s.lower() == unicode(row[0],'utf8').lower():
                return unicode(row[2], 'utf8')
            if unidecode(s).lower() == unidecode(unicode(row[0],'utf8')).lower():
                return unicode(row[2], 'utf8')
            if s.lower() == remove_non_ascii(row[0]).lower():
                return unicode(row[2], 'utf8')
    return s


def matching_countries(entity):
    # further correction for misspellings
    matching_countries = difflib.get_close_matches(entity, country_names, cutoff=0.8,)
    if matching_countries:
        confidence = difflib.SequenceMatcher(None, matching_countries[0], entity).ratio()
        return (matching_countries[0], confidence)


def get_countries(places, spellcheck=False):
    # correcting selling introduces some false positives
    # likelihood of official government documents being spelled incorrectly is low
    countries = []
    for place, label in places:
        if label == 'LOCATION':
            place = correct_country_mispelling(place)
            if spellcheck:
                match = matching_countries(place.lower())
                if match:
                    countries.append((place, match[1]))
            else:
                if place.lower() in country_names:
                    countries.append((title_except(place), 1.0))
    c = set(Counter(name for name, _ in countries).iteritems())
    c_dict = {}
    for country, count in c:
        # gets the probability from before the counter
        c_dict.update({country: {'probability': probability, 'count': count} for name, probability in sorted(countries) if name in country})
    return c_dict


def remove_non_ascii(s): return "".join(i for i in s if ord(i)<128)


def fuzzy_match(s1, s2, max_dist=.8):
    return jellyfish.jaro_distance(s1, s2) >= max_dist

def adjust_probabilities(old_probability, possible_countries):
    if len(set(count for _, count in possible_countries)) <= 1:
        # no change to probabilities when there are no contextual clues
        return [(country, old_probability) for country, _ in possible_countries]

    list_ = []
    for country, count in possible_countries:
        new_probability = old_probability
        if count == 0:
            # only decreases it by a single half if there is no nearby context for it
            decrease = new_probability / 2
            new_probability -= decrease
        for i in range(count):
            # increase probability by half for each context clue in range
            increase = (1.0 - new_probability) / 2
            new_probability += increase
        list_.append((country, new_probability))
    return list_


def remove_word(s, word):
    remove = word
    regex = re.compile(r'\b('+remove+r')\b', flags=re.IGNORECASE)
    out = regex.sub("", s)
    return out


def find_all(a_str, sub):
    start = 0
    while True:
        start = a_str.find(sub, start)
        if start == -1: return
        yield start
        start += len(sub) # use start += 1 to find overlapping matches


def context_adjustment(place, possible_countries, probability, text):
    # get contextual windows revolving around ambiguous place name
#     print('{} could be in {} with a probability of {} for each'.format(place, possible_countries, probability))
    window = 60
    bottom = lambda x: x-window if x-window > 0 else 0
    top = lambda x: x+window if x+window < len(text) else len(text)
#     print indices
    indices = list(find_all(text, place))
    contexts = [text[bottom(i):top(i)] for i in indices]
#     print('{} has surrounding contexts of {}'.format(place, contexts))
#     print
    new_probabilities = []
    while not new_probabilities:
        # waits until any contextual clues are acquired rather than getting every possible contextual clue which can lead to false positives when get multiple copies of same error
        for context in contexts:
            context = remove_word(context, place)
            tokens = nltk.word_tokenize(context)
            codes = [t for t in tokens if t==t.upper() and t.isalpha()]

            # chop off first and last token which are likely not whole words
            tokens = [token.lower() for token in tokens if token.isalpha()][1:-2]
            bi_tokens = bigrams(tokens)
            tri_tokens = trigrams(tokens)
            tokens = tokens + [' '.join(t) for t in bi_tokens] + [' '.join(t) for t in tri_tokens]

            # fix capitalization of state codes
            tokens = [(lambda x: x.upper() if x.upper() in codes else title_except(x))(t) for t in tokens]
#             print('Recognized locations in the context are {}'.format(filter(lambda x: x in [i for i in almost_everything.subdivision.tolist()], tokens)))
            context_countries = []

            # check whether contextual token is a country subdivision
            for i in tokens:
                a = almost_everything[almost_everything.subdivision == i]
                if not a.empty:
                    list_ = a.country_name.tolist()
                    context_countries.extend(list_)
    #                 print('{} could refer to {}'.format(i, list_))

            # use the number of contextual countries that are the same as the ambiguous countries to compute new probabilities
            if context_countries:
                context_count = Counter(context_countries)
    #             print('Counts for each context-country are {}'.format(context_count))
                ambiguous_country_counts = zip(possible_countries, map(lambda x: context_count[x], possible_countries))
#                 print('Counts for ambiguous countries are {}'.format(ambiguous_country_counts))
                new_probabilities.extend(adjust_probabilities(probability, ambiguous_country_counts))
                break # break out of for loop when gather first contextual clue
        break # break out of while loop when there are no contextual clues after looping through all

    # combine multiple contexts into a single count and probability per country
    dict_ = {}
    if new_probabilities:
        country_set = {i[0] for i in new_probabilities}
        for country in country_set:
            probs = [i[1] for i in new_probabilities if i[0] == country]
            count = len(probs)
            probability = probs.pop(0)
            if probs:
                for i in probs:
                    probability = independent_either_probability(probability, i)
            dict_[country] = {'count': count, 'probability': probability}
    else:
        for country in possible_countries:
            dict_[country] = {'count': 1, 'probability': probability}
    return dict_


def independent_either_probability(oldp, newp):
    probability_non_occurrence = (1-oldp) * (1-newp)
    new_probability = 1 - probability_non_occurrence
    return new_probability


def update_countries_with_regions(entities, countries, text):
    # adds countries derived from regions to country list
    subs = pd.DataFrame()
    for entity in {i[0] for i in entities if i[1]=='LOCATION'}:
        a = almost_everything[almost_everything.subdivision == entity]
        if not a.empty:
            subs = pd.concat([subs, a], ignore_index=True)

    if not subs.empty:
        subs.country_name = subs.country_name.apply(standardize_country_name)
        no_dupes = subs.drop_duplicates(['country_name', 'subdivision'])
        for value_count in no_dupes.subdivision.value_counts().iteritems():
            count = value_count[1]
            place = value_count[0]
            probability = 1.0 / count
            if probability == 1.0:
                # only one country exists for a single subdivision
                probability = 0.8 # correcting for imperfect entity parsing
                possible_countries = subs[subs.subdivision == place].country_name.tolist()
                country = possible_countries[0]
                if country in countries:
                    priors = countries[country]
                    new_count = priors['count'] + len(possible_countries)
                    new_probability = independent_either_probability(priors['probability'], probability)
                    countries[country] = {'count': new_count, 'probability': new_probability}
                else:
                    countries[country] = {'count': len(possible_countries), 'probability': probability}
            else:
                # multiple countries exist for a single subdivision
                possible_countries = no_dupes[no_dupes.subdivision == place].country_name.tolist()
                new_probabilities = context_adjustment(place, possible_countries, probability, text)
                for country in possible_countries:
                    if country in countries:
                        priors = countries[country]
                        new_count = priors['count'] + new_probabilities[country]['count']
                        new_probability = independent_either_probability(priors['probability'], new_probabilities[country]['probability'])
                        countries[country] = {'count': new_count, 'probability': new_probability}
                    else:
                        countries[country] = {'count': new_probabilities[country]['count'], 'probability': new_probabilities[country]['probability']}
    return countries


def parse_countries(row):
    countries = get_countries(row[1].entities)
    countries = update_countries_with_regions(row[1].entities, countries, row[1].raw_text)
    return countries


def main():
    df = pd.read_pickle('entities_df')

    pool = Pool()
    result = pool.map(parse_countries, list(df.iterrows()))
    pool.close()

    df['countries'] = result
    df.to_pickle('labels_df')


if __name__ == '__main__':

    country_names = [i.name for i in pycountry.countries]
    country_names = [standardize_country_name(i).lower() for i in country_names]

    subdivision_df = pd.DataFrame.from_csv('GeoLite2-City-Locations.csv', index_col=None, encoding='utf8').dropna(subset=['country_name'])

    s1 = subdivision_df[['country_name', 'subdivision_name']].dropna().rename(columns={'subdivision_name':'subdivision'})
    s1['type'] = 'subdivision'
    s2 = subdivision_df[['country_name', 'subdivision_iso_code']].dropna().rename(columns={'subdivision_iso_code':'subdivision'})
    s2['type'] = 'subdivision_code'
    s3 = subdivision_df[['country_name', 'city_name']].dropna().rename(columns={'city_name':'subdivision'})
    s3['type'] = 'city'
    s4 = subdivision_df[['country_name', 'country_iso_code']].dropna().rename(columns={'country_iso_code':'subdivision'})
    s4['type'] = 'country_code'

    # add countries to 'everything'
    s5 = pd.DataFrame([subdivision_df.country_name.unique()]*2).T
    s5.columns = ['country_name','subdivision']
    s5['type'] = 'country'

    almost_everything = pd.concat([s1,s2,s3,s4,s5], ignore_index=True).drop_duplicates()

    main()
