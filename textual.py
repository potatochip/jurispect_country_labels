'''
text-related functions
'''

import jellyfish
import re
import string
from unidecode import unidecode
import nltk


title_exceptions = ['a', 'an', 'the', 'and', 'but', 'or', 'for' 'nor', 'on', 'at', 'to', 'from', 'by', 'of']
title_abbreviations = ['nasa', 'usa']


def remove_non_ascii(s):
    '''
    removes any non-standard ascii characters (like accented characters) from a string
    '''
    return "".join(i for i in s if ord(i)<128)


def standardize_text(s):
    pass


def string_stripper(s):
    # Get rid of extra white space in front, back and middle
    stripped = ' '.join(s.split())
    # Get rid of all trailing non-letter symbols
    while re.search(r'\W+$', stripped, flags=re.UNICODE) is not None:
        stripped = stripped[:-1]
    return stripped


def process_string(s):
    lower = s.lower()
    # changes special chracters to standard representation
    # works well for latin based alphabets. not so much for others.
    standard_ascii = unidecode(lower)
    # leaves special characters as their ascii representation
    # standard_ascii = lower.encode('utf8')
    no_punc = standard_ascii.translate(None, string.punctuation.replace('&', ''))
    stripped = string_stripper(no_punc)
    return unicode(stripped, 'utf8')


def get_contexts(term, text):
    # get contextual windows revolving around term for resolving ambiguity
    window = 30
    bottom = lambda x: x-window if x-window > 0 else 0
    top = lambda x: x+window if x+window < len(text) else len(text)
    indices = list(find_all(text, term))
    contexts = [text[bottom(i):top(i)] for i in indices]
    return contexts


def tokenize(text):
    tokens = nltk.word_tokenize(text)
    tokens = [token.lower() for token in tokens if token.isalpha()]
    return tokens


def simple_match(s1, s2):
    '''
    returns bool of whether two strings are identical after processing
    '''
    return s1 == s2


def phonetic_match(s1, s2):
    '''
    returns bool of whether two strings are phonetically identical after processing
    '''
    return jellyfish.metaphone(s1) == jellyfish.metaphone(s2)


def fuzzy_match(s1, s2, max_dist=.8):
    '''
    returns bool of whether two unicode strings are similar within max_dist of each other
    '''
    return jellyfish.jaro_distance(s1, s2) >= max_dist


def titlecase(s):
    '''
    better title capitalization than python's built-in
    '''
    word_list = re.split(' ', s.lower())
    final = []
    for ix, word in enumerate(word_list):
        if word.count('.') > 1:
            # fix abbreviations correctly
            word = word.upper()
        elif word in title_abbreviations:
            # fix known abbreviations that aren't represented by periods between each letter
            word = word.upper()
        elif '-' in word:
            location = word.find('-')
            word = word.capitalize()
            word = word.replace(word[location+1], word[location+1].upper())
        elif word[0] in ['(', '[']:
            word = word.replace(word[1], word[1].upper())
        elif "d'" in word.lower():
            location = word.lower().find("d'")
            word = word.capitalize()
            word = word.replace(word[location], word[location].lower())
            word = word.replace(word[location+2], word[location+2].upper())
        elif ix == 0:
            if word in ['us']:
                word = word.upper()
            else:
                word = word.capitalize()
        elif word in title_exceptions:
            word = word.lower()
        else:
            word = word.capitalize()
        final.append(word)
    return " ".join(final)


def remove_words(s, word):
    '''
    remove all occurences of a word from a string with proper space correction
    '''
    remove = word
    regex = re.compile(r'\b('+remove+r')\b', flags=re.IGNORECASE)
    out = regex.sub("", s)
    return out


def find_all(a_str, sub):
    '''
    returns all the indices of a sub-string in a string
    '''
    start = 0
    while True:
        start = a_str.find(sub, start)
        if start == -1: return
        yield start
        start += len(sub) # use start += 1 to find overlapping matches


def smart_find(haystack, needle):
    '''
    returns whether a string (haystack) contains a substring (needle)
    works on multi-word substrings
    '''
    if haystack.startswith(needle+" "):
        return True
    if haystack.endswith(" "+needle):
        return True
    if haystack.find(" "+needle+" ") != -1:
        return True
    return False
