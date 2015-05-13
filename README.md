# wattsbot
This is an experiment in generative poetry with rhyme and meter. 

Example output, based on the psalms and hymns of Isaac Watts, can be found on Twitter at @watts_ebooks. 

## Usage

Currently only usable from the python shell. If parsedpsalms.txt and wattsbot.py are in an accessible directory, then:

- `execfile("wattsbot.py")` to load everything.
- `m = VerseMarkov(open("parsedpsalms.txt"))` creates a model based on the text of Watt's hymns.
- `m.generate(length, rhyme=None)` generates a line of `length` syllables — 6 and 8 are ideal. If a `rhyme` is specified, the line will rhyme with it. If no rhyming line can be generated, it will return `None`.
- `m.cmverse(), m.lmverse()` and `m.smverse()` generate full stanzas in Common Meter, Long Meter and Short Meter respectively. (This may take a long time. They will print their progress to the screen occasionally.) 

Some representative sample output:
```
>>> m.cmverse()
lord, thou hast searched and seen me through,
he doth my soul detest
in jesus' blood, we're marching through
immanuel's ground to rest.

>>> m.lmverse()
for thou alone dost wondrous things,
for thou alone dost thou not raise
my panting heart cries out for god;
my god! how wondrous are his ways!

>>> m.smverse()
the lord my shepherd is,
i shall arise to praise
and will the growing numbers end,
the numbers of thy praise.
```

## Who is this guy?

Watts was probably the greatest author of hymn lyrics in English. (The words to "Joy to the World," 
"Oh God, Our Help in Ages Past" and "This is the Day the Lord Has Made" are all his, and he is the
best-represented poet in *The Sacred Harp.*) 

There are a few things that make him a convenient author to imitate.
- Nearly everything he wrote has a *consistent structure:* four-line rhymed iambic stanzas, mostly Common Meter 
(a.k.a. "things you can sing to the tune of the Gilligan's Island theme song").
- Unlike Emily Dickinson, the most famous user of Common Meter, his scansion and rhyming is *highly regular.*
- He revisits *a small set of images* — mostly Biblical or natural — again and again in his poetry.
- He was *highly prolific,* and everything he wrote is in the public domain and available online.

The consistent rhyme and meter make it easy for a program to scan his poems correctly. His prolific output and
repetitive imagery solves some of the problems with data sparseness that can come up doing this sort of thing
with a limited source corpus.


