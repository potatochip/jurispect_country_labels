from nltk.tokenize.punkt import PunktSentenceTokenizer, PunktTrainer
import pickle
import pandas as pd


df = pd.read_pickle('docs_df')
docs = df.raw_text.tolist()

trainer = PunktTrainer()

trainer.ABBREV = 0.3
"""cut-off value whether a 'token' is an abbreviation"""

trainer.IGNORE_ABBREV_PENALTY = False
"""allows the disabling of the abbreviation penalty heuristic, which
exponentially disadvantages words that are found at times without a
final period."""

trainer.ABBREV_BACKOFF = 5
"""upper cut-off for Mikheev's(2002) abbreviation detection algorithm"""

trainer.COLLOCATION = 7.88
"""minimal log-likelihood value that two tokens need to be considered
as a collocation"""

trainer.SENT_STARTER = 30
"""minimal log-likelihood value that a token requires to be considered
as a frequent sentence starter"""

trainer.INCLUDE_ALL_COLLOCS = False
"""this includes as potential collocations all word pairs where the first
word ends in a period. It may be useful in corpora where there is a lot
of variation that makes abbreviations like Mr difficult to identify."""

trainer.INCLUDE_ABBREV_COLLOCS = False
"""this includes as potential collocations all word pairs where the first
word is an abbreviation. Such collocations override the orthographic
heuristic, but not the sentence starter heuristic. This is overridden by
INCLUDE_ALL_COLLOCS, and if both are false, only collocations with initials
and ordinals are considered."""
""""""

trainer.MIN_COLLOC_FREQ = 1
"""this sets a minimum bound on the number of times a bigram needs to
appear before it can be considered a collocation, in addition to log
likelihood statistics. This is useful when INCLUDE_ALL_COLLOCS is True."""

progress = ProgressBar()
for doc in progress(docs):
    trainer.train(doc, finalize=False, verbose=False)

print "Finalizing training..."
trainer.finalize_training(verbose=True)
print "Training done."

params = trainer.get_params()
with open('sentence_tokenizer_params.pkl', 'wb') as f:
    pickle.dump(params, f, protocol=pickle.HIGHEST_PROTOCOL)
print "Params: %s" % repr(params)

# set custom parameters
# extra_collocations = {(u'sec', u'##number##')}
# extra_sentence_starters = {u'(##number##)'}
# extra_abbreviations = {u'U.S.C', u'usc'}

# add in custom collocations etc
# params.collocations = params.collocations | extra_collocations
# params.sent_starters = params.sent_starters | extra_sentence_starters

tokenizer = PunktSentenceTokenizer(params)

with open("sentence_tokenizer.pkl", mode='wb') as f:
        pickle.dump(tokenizer, f, protocol=pickle.HIGHEST_PROTOCOL)
