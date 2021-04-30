# pyknp-eventgraph

**EventGraph** is a development platform for high-level NLP applications in Japanese.
The core concept of EventGraph is event, a language information unit that is closely related to predicate-argument structure but more application-oriented.
Events are linked to each other based on their syntactic and semantic relations.

## Requirements

- Python 3.6 or later
- pyknp
- graphviz

## Installation

To install pyknp-eventgraph, use `pip`.

```
$ pip install pyknp-eventgraph
```

## Quick Tour

### Step 1: Create an EventGraph

An EventGraph is built on language analysis given in a KNP format.

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
print(evg)  # <EventGraph, #sentences: 2, #events: 3, #relations: 1>
```

### Step 2: Extract Information

Users can obtain various information about language analysis via a simple interface.

#### Step 2.1: Sentence

```python
# Extract sentences.
sentences = evg.sentences
print(sentences)
# [
#   <Sentence, sid: 1, ssid: 0, surf: 彼女は海外勤務が長いので、英語がうまいに違いない。>,
#   <Sentence, sid: 2, ssid: 1, surf: 私はそう確信していた。>
# ]

# Convert a sentence into various forms.
sentence = evg.sentences[0]
print(sentence.surf)   # 彼女は海外勤務が長いので、英語がうまいに違いない。
print(sentence.mrphs)  # 彼女 は 海外 勤務 が 長い ので 、 英語 が うまい に 違いない 。
print(sentence.reps)   # 彼女/かのじょ は/は 海外/かいがい 勤務/きんむ が/が 長い/ながい ので/ので 、/、 英語/えいご が/が 上手い/うまい に/に 違い無い/ちがいない 。/。
```

#### Step 2.2: Event

```python
# Extract events.
events = evg.events
print(events)
# [
#   <Event, evid: 0, surf: 海外勤務が長いので、>,
#   <Event, evid: 1, surf: 彼女は英語がうまいに違いない。>,
#   <Event, evid: 2, surf: 私はそう確信していた。>
# ]

# Convert an event into various forms.
event = evg.events[0]
print(event.surf)              # 海外勤務が長いので、
print(event.mrphs)             # 海外 勤務 が 長い ので 、
print(event.normalized_mrphs)  # 海外 勤務 が 長い
print(event.reps)              # 海外/かいがい 勤務/きんむ が/が 長い/ながい ので/ので 、/、
print(event.normalized_reps)   # 海外/かいがい 勤務/きんむ が/が 長い/ながい
print(event.content_rep_list)  # ['海外/かいがい', '勤務/きんむ', '長い/ながい']

# Extract an event's PAS.
pas = event.pas
print(pas)            # <PAS, predicate: 長い/ながい, arguments: {ガ: 勤務/きんむ}>
print(pas.predicate)  # <Predicate, type: 形, surf: 長い>
print(pas.arguments)  # defaultdict(<class 'list'>, {'ガ': [<Argument, case: ガ, surf: 勤務が>]})

# Extract an event's features.
features = event.features
print(features)  # <Features, modality: None, tense: 非過去, negation: False, state: 状態述語, complement: False>
```

#### Step 2.3: Event-to-event Relation

```python
# Extract event-to-event relations.
relations = evg.relations
print(relations)  # [<Relation, label: 原因・理由, modifier_evid: 0, head_evid: 1>]

# Take a closer look at an event-to-event relation
relation = relations[0]
print(relation.label)     # 原因・理由
print(relation.surf)      # ので
print(relation.modifier)  # <Event, evid: 0, surf: 海外勤務が長いので、>
print(relation.head)      # <Event, evid: 1, surf: 彼女は英語がうまいに違いない。>
```

### Step 3: Seve/Load an EventGraph

Users can save and load an EventGraph by serializing it as a JSON object.

```python
# Save an EventGraph as a JSON file.
evg.save('evg.json')

# Load an EventGraph from a JSON file.
with open('evg.json') as f:
    evg = EventGraph.load(f)
```

### Step 4: Visualize an EventGraph

Users can visualize an EventGraph using [graphviz](https://graphviz.org/).

```python
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

evg = EventGraph.build(analysis)
print(evg)  # <EventGraph, #sentences: 1, #events: 2, #relations: 1>

# Investigate the relation.
relation = evg.relations[0]
print(relation)           # <Relation, label: 連体修飾, modifier_evid: 0, head_evid: 1>
print(relation.modifier)  # <Event, evid: 0, surf: もっととろみが持続する>
print(relation.head)      # <Event, evid: 1, surf: 作り方をして欲しい。>

# To merge modifier events, enable `include_modifiers`.
print(relation.head.surf)                           # 作り方をして欲しい。
print(relation.head.surf_(include_modifiers=True))  # もっととろみが持続する作り方をして欲しい。

# Other formats also support `include_modifiers`.
print(relation.head.mrphs_(include_modifiers=True))  # もっと とろみ が 持続 する 作り 方 を して 欲しい 。
print(relation.head.normalized_mrphs_(include_modifiers=True))  # もっと とろみ が 持続 する 作り 方 を して 欲しい
```

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
