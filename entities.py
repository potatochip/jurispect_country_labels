'''
grabs stanford named entities from raw text

3 class:	Location, Person, Organization
4 class:	Location, Person, Organization, Misc
7 class:	Time, Location, Organization, Person, Money, Percent, Date
These models each use distributional similarity features, which provide some performance gain at the cost of increasing their size and runtime.

The following other models are available at http://nlp.stanford.edu/software/CRF-NER.shtml
Models with no distsim features
Models which ignore capitalization
German NER
Spanish CoreNLP models
Chinese NER
'''

import pandas as pd
from multiprocessing import Pool
import nltk
from nltk.tag.stanford import StanfordNERTagger
from nltk import pos_tag
from nltk.chunk import conlltags2tree
from nltk.tree import Tree


st = StanfordNERTagger('/Users/amangum/stanford-ner/classifiers/english.all.3class.distsim.crf.ser.gz', '/Users/amangum/stanford-ner/stanford-ner.jar')


def stanfordNE2BIO(tagged_sent):
    bio_tagged_sent = []
    prev_tag = "O"
    for token, tag in tagged_sent:
        if tag == "O": #O
            bio_tagged_sent.append((token, tag))
            prev_tag = tag
            continue
        if tag != "O" and prev_tag == "O": # Begin NE
            bio_tagged_sent.append((token, "B-"+tag))
            prev_tag = tag
        elif prev_tag != "O" and prev_tag == tag: # Inside NE
            bio_tagged_sent.append((token, "I-"+tag))
            prev_tag = tag
        elif prev_tag != "O" and prev_tag != tag: # Adjacent NE
            bio_tagged_sent.append((token, "B-"+tag))
            prev_tag = tag

    return bio_tagged_sent


def stanfordNE2tree(ne_tagged_sent):
    bio_tagged_sent = stanfordNE2BIO(ne_tagged_sent)
    sent_tokens, sent_ne_tags = zip(*bio_tagged_sent)
    sent_pos_tags = [pos for token, pos in pos_tag(sent_tokens)]

    sent_conlltags = [(token, pos, ne) for token, pos, ne in zip(sent_tokens, sent_pos_tags, sent_ne_tags)]
    ne_tree = conlltags2tree(sent_conlltags)
    return ne_tree


def find_entities(text):
    tokens = nltk.word_tokenize(text)

    places = []

    ne_tagged_sent = st.tag(tokens)
    ne_tree = stanfordNE2tree(ne_tagged_sent)
    for ne in ne_tree:
        if isinstance(ne, Tree): # If subtree is a noun chunk, i.e. NE != "O"
            if ne.label() in ['LOCATION', 'PERSON', 'ORGANIZATION']:
                ne_label = ne.label()
                ne_string = u' '.join([token for token, pos in ne.leaves()])
                places.append((ne_string, ne_label))

    return places


def find_entities_pool(documents):
    pool = Pool()
    result = pool.map(find_entities, documents)
    pool.close()
    return result


def main():
    df = pd.read_pickle('docs_df')

    df[['title', 'toc_subject']] = df[['title', 'toc_subject']].fillna('')
    documents = df.title + '\n' + df.toc_subject + '\n' + df.topics.apply(lambda x: ' '.join(x)) + '\n' + df.raw_text

    pool = Pool()
    result = pool.map(find_entities, documents.tolist())
    pool.close()

    df['entities'] = result
    df.to_pickle('entities_df')


if __name__ == '__main__':
    main()
