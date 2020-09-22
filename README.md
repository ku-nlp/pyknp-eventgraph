# pyknp-eventgraph

**EventGraph** is a development platform for high-level NLP applications in Japanese.
The core concept of EventGraph is event, a language information unit that is closely related to predicate-argument structure but more application-oriented.
Events are linked to each other based on their syntactic and semantic relations.

## Requirements

- Python 3.6 or later
- pyknp: 0.4.1
- graphviz: 0.10.1

## Installation

To install pyknp-eventgraph, use `pip`.

```
$ pip install pyknp-eventgraph
```

or

```
$ python setup.py install
```

## Basic Usage

```python
# Add imports.
from pyknp import KNP
from pyknp_eventgraph import EventGraph

# Parse a document.
document = ['彼女は海外勤務が長いので、英語がうまいに違いない。', '私はそう確信していた。']
knp = KNP()
analysis = [knp.parse(sentence) for sentence in document]

# Create an EventGraph.
evg = EventGraph.build(analysis)

# Print the EventGraph.
print(evg)  # EventGraph(#sentences: 2, #events: 3, #relations: 1)

# Print sentences.
print(evg.sentences[0])  # Sentence(sid: 1, ssid: 0, surf: 彼女は海外勤務が長いので、英語がうまいに違いない。)
print(evg.sentences[1])  # Sentence(sid: 2, ssid: 1, surf: 私はそう確信していた。)

# Sentences are iterable.
for sentence in evg.sentences:
    pass

# Print a sentence in different forms.
sentence = evg.sentences[0]
print(sentence.mrphs)  # 彼女 は 海外 勤務 が 長い ので 、 英語 が うまい に 違いない 。
print(sentence.reps)   # 彼女/かのじょ は/は 海外/かいがい 勤務/きんむ が/が 長い/ながい ので/ので 、/、 英語/えいご が/が 上手い/うまい に/に 違い無い/ちがいない 。/。

# Print events.
print(evg.events[0])  # Event(evid: 0, surf: 海外勤務が長いので、)
print(evg.events[1])  # Event(evid: 1, surf: 彼女は英語がうまいに違いない。)
print(evg.events[2])  # Event(evid: 2, surf: 私はそう確信していた。)

# Events are also iterable.
for event in evg.events:
    pass

# Print an event in different forms.
event = evg.events[0]
print(event.surf)              # 海外勤務が長いので、
print(event.mrphs)             # 海外 勤務 が 長い ので 、
print(event.normalized_mrphs)  # 海外 勤務 が 長い
print(event.reps)              # 海外/かいがい 勤務/きんむ が/が 長い/ながい ので/ので 、/、
print(event.normalized_reps)   # 海外/かいがい 勤務/きんむ が/が 長い/ながい
print(event.content_rep_list)  # ['海外/かいがい', '勤務/きんむ', '長い/ながい']

# Print an event's PAS information.
print(event.predicate)        # Predicate(type: 形, surf: 長い)
print(event.arguments['ガ'])  # [Argument(case: ガ, surf: 勤務が)]

# Print an event's features.
print(event.features)  # Features(modality: None, tense: 非過去, negation: False, state: 状態述語, complement: False)

# Print relations between events.
relation = evg.relations[0]
print(relation)           # Relation(label: 原因・理由, modifier_evid: 0, head_evid: 1)
print(relation.modifier)  # Event(evid: 0, surf: 海外勤務が長いので、)
print(relation.head)      # Event(evid: 1, surf: 彼女は英語がうまいに違いない。)

# Relations are iterable, too.
for relation in evg.relations:
    pass

# Access to pyknp's objects.
print(type(sentence.blist))                # <class 'pyknp.knp.blist.BList'>
print(type(event.predicate.tag))           # <class 'pyknp.knp.tag.Tag'>
print(type(event.arguments['ガ'][0].tag))  # <class 'pyknp.knp.tag.Tag'>
print(type(event.arguments['ガ'][0].arg))  # <class 'pyknp.knp.pas.Argument'>

# Convert an EventGraph into a dictionary.
dct = evg.to_dict()  # {"sentences": ..., "events": ...}

# Save an EventGraph as a JSON file.
evg.save('evg.json')

# Load an EventGraph from a JSON file.
with open('evg.json') as f:
    evg_ = EventGraph.load(f)

# Visualize an EventGraph.
from pyknp_eventgraph import make_image
make_image(evg, 'evg.svg')  # Currently, only supports 'svg'.
```

## Advanced Usage

### Merging modifiers

By merging a modifier event to the modifiee, users can construct a larger information unit.

```python
from pyknp import KNP
from pyknp_eventgraph import EventGraph

document = ['もっととろみが持続する作り方をして欲しい。']
knp = KNP()
analysis = [knp.parse(sentence) for sentence in document]

# Print some information.
evg = EventGraph.build(analysis)
print(evg)  # EventGraph(#sentences: 1, #events: 2, #relations: 1)

# Investigate what the relation is.
relation = evg.relations[0]
print(relation)           # Relation(label: 連体修飾, modifier_evid: 0, head_evid: 1)
print(relation.modifier)  # Event(evid: 0, surf: もっととろみが持続する)
print(relation.head)      # Event(evid: 1, surf: 作り方をして欲しい。)

# To merge modifiers' tokens, enable `include_modifiers`.
print(relation.head.surf)                           # 作り方をして欲しい。
print(relation.head.surf_(include_modifiers=True))  # もっととろみが持続する作り方をして欲しい。

# Other formats also support `include_modifiers`.
print(relation.head.mrphs_(include_modifiers=True))  # もっと とろみ が 持続 する 作り 方 を して 欲しい 。
print(relation.head.normalized_mrphs_(include_modifiers=True))  # もっと とろみ が 持続 する 作り 方 を して 欲しい
```

## Advanced Usage

### Binary serialization

When an EventGraph is serialized in a JSON format, it will lose some functionality, including access to KNP objects and modifier merging.
To keep full functionality, use Python's pickle utility for serialization.

```python
# Save an EventGraph using Python's pickle utility.
evg.save('evg.pkl', binary=True)

# Load an EventGraph using Python's pickle utility.
with open('evg.pkl', 'rb') as f:
    evg_ = EventGraph.load(f, binary=True)
```

## CLI

### EventGraph Construction

```
$ echo '彼女は海外勤務が長いので、英語がうまいに違いない。' | jumanpp | knp -tab | evg -o example-eventgraph.json
```

### EventGraph Visualization

```
$ evgviz example-eventgraph.json example-eventgraph.svg
```

## Documents

[https://pyknp-eventgraph.readthedocs.io/en/latest/](https://pyknp-eventgraph.readthedocs.io/en/latest/)

## Authors

- Kurohashi-Kawahara Lab, Kyoto University.
- contact@nlp.ist.i.kyoto-u.ac.jp
