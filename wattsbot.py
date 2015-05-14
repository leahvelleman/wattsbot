#!/usr/bin/env python
# -*- coding: utf-8 -*-
# TODO
# "o'er"
#
# allow indeterminacy in syllabifying a line, and only accept parses that
# come out to an even number of syllables
#
# allow for backtracking if we end up with a KeyError while generating text
#   
# lots of possible improvements related to rhyming:
#   - handle near-rhymes in a tolerable way?
#   - prefer rhymes which watts actually uses?
#
# words shouldn't rhyme with themselves
#
# capitalization
#
# pull in other metrical psalters
#
# choose seed words that have started a STANZA not just a line?
# or 
"""
A Markov chain model with useful properties for generating poetry.

The model has two distinctive features.  First, it is a *reverse* ngram model.
That is, the estimated probability of a word depends on the *following* n
words, and in generating text we work from right to left rather than from left
to right. This facilitates rhyming.
      
Second, the model takes meter into account, though at present only in a crude
way. It assumes the training data will be metrically consistent.
 
       - At a bare minimum, the training data should contain verse with only
         one foot type --- most likely either all iambs or all trochees. (This
         already rules out certain Greek meters, or Hopkins-style sprung meter,
         which uses multiple foot types in a single line.)

       - Ideally, the training data should have lines that are consistent in
         other ways: position of caesurae, amount and type of enjambment, etc.
 
If these assumptions are met, then we can generate text which approximates the
meter of the training text without actually modeling the rules of scansion 
directly.

# DEPENDENCIES

The NLTK implementation of the CMU pronunciation dictionary is used for
counting syllables and for determining whether words rhyme. It is *not* used
for scansion.  If words are scanned differently in the training text than they
are in the dictionary (see e.g. some hymnodists' habit of scanning "Jesus" as a
iamb, as in "Jesus my all to heav'n is gone"), the scansion found in the
training text will be used.

# FEATURES AND PARAMETERS

The probability of a word is calculated based on two features:

      a. The `environment`, consisting of the `n-1` words following the target
         word.

      b. The `offset`, consisting of the distance in syllables between the
         target word and the beginning of the line.
  
There are two important parameters used in training the model:

     `n` is the size of n-gram on which the model should be based.

     `k` is a measure of how metrically "exacting" the model should be.  In
         general, `k` should divide evenly into the number of syllables in the
         (most common type of) line found in the training text.
         
         Low values of `k` produce poems with a lot of spurious enjambment ---
         i.e.  poems that are much more likely than the training corpus to
         contain sentences that wrap around from one line to the next, or end
         in mid-line.

         High values of `k` reduce spurious enjambment, but also constrain the
         model more tightly, raising the risk that it paint itself into a
         corner where it is unable to generate any more words.
         
Internally, `k` is applied as a modulus to the offset in both training and
generation. This determines how much information about the offset is kept,
and how much is thrown away.

For instance, consider a model trained on iambic tetrameter, with the intention
of generating eight-syllable lines. There are four useful settings for `k`:
    
 `k = 1` The model will ignore *all* information about the offset. Generated
         lines will have eight syllables, but will not be in iambs.
 
 `k = 2` The model will only pay attention to the difference between even and
         odd (i.e. stressed and unstressed) syllables. The output will be 
         iambic, but will feature a lot of enjambment, since in generating
         text it will not "know" whether or not it is at a line boundary.

 `k = 4` The model will additionally pay attention to whether a word is at the
         beginning or end of a hemistich (a "half-line" of four syllables).
         This will reduce enjambment somewhat.

 `k = 8` The model will additionally pay attention to the location of a word
         within a full eight-syllable line. This will reduce enjambment to
         roughly the level found in the training text, since the model now
         "knows" exactly where it is relative to line boundaries.
         
There are three additional parameters that apply in generating text.

 `length` is the number of syllables to be generated. This should be an even
          multiple of the `k` value on which the model was trained. The most
          likely value for `length` is the length in syllables of a single line
          (e.g.  8 for iambic tetrameter).

   `seed` is the environment for the first word to be generated. (This is useful
          in generating multi-line poems. Remember that we generate backwards, 
          from the end of the poem towards the start. Thus, the `seed` for line n
          should be the initial words of line n+1.)

  `rhyme` is a target word that the first word to be generated should rhyme with.
          For instance, in generating a poem with an ABCB rhyme scheme, the
          `rhyme` for generating line 2 should be the final word of line 4.


"""



import random
import re
from nltk.corpus import cmudict
from collections import defaultdict

d = cmudict.dict()
PUNCTUATION = " .,;:!?\"'"

def get_rhymable_part(phones):
  """Returns the rhymable part of a list of CMUDict-style phones -- that is,
  the part beginning with the last vowel bearing primary or secondary stress,
  and extending to the end of the phone list."""
  out = []
  for i in reversed(range(len(phones))):
    out.insert(0, phones[i].strip("012")) # .strip("012") here means that
                                          # extracted rimes will not actually
                                          # contain stress marks.  The result
                                          # is that a syllable with secondary
                                          # stress can rhyme with one with
                                          # primary stress: e.g. álbatròss can
                                          # rhyme with móss.
    if phones[i].endswith(("1", "2")):
      return out

def find_rhymes(w1):
  """Given a word in English orthography, returns a list of other words which 
  rhyme with it. More specifically, returns words whose rhymable part matches
  the rhymable part of at least one pronunciation of the input word. Strips
  punctuation from its input if necessary."""
  w1 = w1.strip(PUNCTUATION)
  items = [(k, v) for k in d.keys() for v in d[k]]
  w1rimes = [get_rhymable_part(phones) for word, phones in items if word == w1]
  rhymes = [word for word, phones in items if get_rhymable_part(phones) in w1rimes]
  return rhymes

def filter_rhymes(candidates, rhyme):
  if rhyme is not None:
    rhymes = find_rhymes(rhyme)
    candidates = [word for word in candidates if word in rhymes]
  return candidates

def syllable_count(word):
  """Given a word in English orthography, returns an estimated syllable count.
  If possible, it gets the count from CMUDict. If no CMUDict entry exists, it
  uses a slapdash set of fallback rules. Strips punctuation from its input if
  neessary."""
  # TODO: When adding indeterminacy in syllabification, make this return a list of
  # possible counts.
  word = word.strip(PUNCTUATION)
  try:
    pronunciation = d[word][0]
    return len([ph for ph in pronunciation if ph[-1].isdigit()])
  except KeyError:                        # Fallback rules:
    word = re.sub("e$", "", word)         # Ignore final E
    word = re.sub("[aeiou]", "V", word)   # A, E, I, O and U are vowels
    word = re.sub("y$", "V", word)        # Final Y is a vowel
    word = re.sub("[^V]y[^V]", "V", word) # Y between non-vowels is a vowel TODO FIX THIS
    word = re.sub("V+", "V", word)        # Vowel sequences are a single syllable
    return word.count("V")

def insert_counts(line):
  """Given a line of verse in English orthography, return a list of 
  (word, count) pairs, where count is the estimated number of syllables in
  word."""
  # TODO: When adding indeterminacy in syllabification, make this handle lists
  # of possible counts, and return lists of possible lists of (word, count) pairs.
  line = line.split()
  k = 0
  out = []
  for word in line:
    word = word.lower()
    k += syllable_count(word)
    out.append((word, k))
  return out

class VerseMarkov(object):
  
  def __init__(self, source, n=3):
    self.cache = defaultdict(list)
    self.line_starts= []
    self.n = n
    if type(source) is str:
      self.data = source
    if type(source) is file:
      source.seek(0)
      self.data = source.read()
    self.words = self.read_words()
    self.digest()

  def read_words(self):
    lines = [insert_counts(line) for line in self.data.split("\n")]
    words = [word for line in lines for word in line]
    return words

  def ngrams(self, n):
    words = [w[0] for w in self.words]
    offsets = [w[1] for w in self.words]
    rest = zip(*[words[i:] for i in range(1,n)])
    return zip(words, offsets, rest)

  def digest(self):
    for result, offset, environment in self.ngrams(self.n):
      key = environment + (offset % 4,)
      if key in self.cache:
        self.cache[key].append(result)
      else:
        self.cache[key] = [result]
    for line in self.data.split("\n"):
      if line.strip() is not "":
        start = line.strip().split()[:2]
        self.line_starts.append([start[0].lower(), start[1].lower()])

      
  def get_fallback_candidates(self, environment, offset, rhyme = None):
    keys = [k for k in self.cache.keys() if k[0] == environment[0] and k[2] == offset % 4]
    candidates = sum([self.cache[k] for k in keys], [])
    candidates = filter_rhymes(candidates, rhyme)
    return candidates

  def get_candidates(self, environment, offset, rhyme = None):
    key = tuple(environment) + (offset % 4,)
    candidates = filter_rhymes(self.cache[key], rhyme)
    if candidates == []:
      candidates = self.get_fallback_candidates(environment, offset, rhyme)
    return candidates

  def draw_word(self, environment, offset, rhyme = None):
    candidates = self.get_candidates(environment, offset, rhyme)
    if candidates == []:
      return None
    return random.choice(candidates)

  def generate(self, length, seed = None, rhyme = None, tries = 10):
    """ Generate a line of `length` syllables, optionally constrained by
    a given `seed` and a word with which it must `rhyme`. This is a stochastic
    process not guaranteed to succeed, since in generating we can paint ourselves
    into a corner. Rather than backtracking, we just start over every time this
    happens, up to a specified number of `tries`.
    """

    # Repeat as long as permitted
    while tries > 0:

      # If no seed is specified, try a different one each time.
      if seed is None:
        environment = random.choice(self.line_starts)
      else:
        environment = seed

      offset = length
      result = ""
      output = []
      current_rhyme = rhyme

      # Until we have generated (at least) enough syllables, keep drawing words
      while offset > 0:
        result = self.draw_word(environment, offset, current_rhyme)
        if result is None:
          break
        offset -= syllable_count(result)
        output.insert(0, result)
        environment = [result] + environment[:-1]
        current_rhyme = None

      # If we have generated *exactly* enough syllables we have succeeded. If not, try again.
      if sum(map(syllable_count, output)) == length:
        return output
      else:
        tries -= 1
        pass

    return None

  def cmverse(self):
    while True:
      l4 = self.generate(6)
      print l4
      l3 = self.generate(8, seed = [l4[0], l4[1]])
      print l3
      if l3 is not None:
        l2 = self.generate(6, rhyme = l4[-1])
        print l2
        if l2 is not None:
          l1 = self.generate(8)
          return l1, l2, l3, l4

  def lmverse(self):
    while True:
      l4 = self.generate(8)
      print l4
      l3 = self.generate(8, seed = [l4[0], l4[1]])
      print l3
      if l3 is not None:
        l2 = self.generate(8, seed = [l3[0], l3[1]], rhyme = l4[-1])
        print l2
        if l2 is not None:
          l1 = self.generate(8, seed = [l2[0], l2[1]])
          print '\n'.join([" ".join(l1), " ".join(l2), " ".join(l3), " ".join(l4)])
          return

  def smverse(self):
    while True:
      l4 = self.generate(6)
      print l4
      l3 = self.generate(8, seed = [l4[0], l4[1]])
      print l3
      if l3 is not None:
        l2 = self.generate(6, seed = [l3[0], l3[1]], rhyme = l4[-1])
        if l2 is None:
          l2 = self.generate(6, rhyme = l4[-1])
        print l2
        if l2 is not None:
          l1 = self.generate(6, seed = [l2[0], l2[1]])
          return l1, l2, l3, l4

a = VerseMarkov(open("parsedpsalms.txt"))
    


