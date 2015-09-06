import pandas as pd
from multiprocessing import Pool
import nltk
from nltk.tag.stanford import StanfordNERTagger
from nltk import pos_tag
from nltk.chunk import conlltags2tree
from nltk.tree import Tree
# from collections import Counter


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
    # stanford tagger takes 2.45 seconds vs 2.38 seconds for standard tagger

    tokens = nltk.word_tokenize(text)
    # tokens = [w for w in nltk.word_tokenize(text) if w.isalpha()]
    # tokens = nltk.word_tokenize(unidecode(text).translate(None, string.punctuation))
    # tokens = text.split()

    places = []

    # stanford tagger
    ne_tagged_sent = st.tag(tokens)
    ne_tree = stanfordNE2tree(ne_tagged_sent)
    for ne in ne_tree:
        if isinstance(ne, Tree): # If subtree is a noun chunk, i.e. NE != "O"
            if ne.label() in ['LOCATION', 'PERSON', 'ORGANIZATION']:
                ne_label = ne.label()
                ne_string = u' '.join([token for token, pos in ne.leaves()])
                places.append((ne_string, ne_label))

    # c = Counter((entity, label) for entity, label in places)
    # return {(entity, label, count) for (entity, label), count in c.items()}
    return places


def main():
    df = pd.read_pickle('docs_df')

    pool = Pool()
    result = pool.map(find_entities, df.raw_text.tolist())
    pool.close()

    df['entities'] = result
    df.to_pickle('entities_df')


if __name__ == '__main__':
    main()
