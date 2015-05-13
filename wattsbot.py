import random
import re
from nltk.corpus import cmudict

d = cmudict.dict()

# TODO
#   "o'er"
#   allow indeterminacy in syllabifying a line, and only accept parses that
#     come out to an even number of syllables
#   allow for backtracking if we end up with a KeyError while generating
#   allow for parsing on larger ngrams than 2


def count(word):
  word = word.strip(" .,;:!?")
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
  line = line.split()
  k = 0
  out = []
  for word in line:
    word = word.lower()
    k += count(word)
    out.append((word, k))
  return out

class VerseMarkov(object):

  def __init__(self, source, n=3):
    self.cache = {}
    self.line_ends = []
    self.n = n
    if type(source) is str:
      self.data = source
    if type(source) is file:
      f.seek(0)
      self.data = f.read()
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
        end = line.strip().split()[-(self.n-1):]
        self.line_ends.append(end)
      

  def generate(self, length):
    finished = False
    while not finished:
      try: 
        environment = random.choice(self.line_ends)
        offset = length - sum(map(count, environment))
        result = ""
        output = []
        while offset > 0:
          print environment, offset
          key = tuple(environment) + (offset % 4,)
          result = random.choice(self.cache[key])
          offset -= count(result)
          output = [environment.pop()] + output
          environment = [result] + environment
        output = environment + output
        if sum(map(count, output)) == length:
          finished = True
      except:
        pass
    return " ".join(output)
      



a = VerseMarkov(open("parsedpsalms.txt"))
    


