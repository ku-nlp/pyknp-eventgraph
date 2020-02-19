# pyknp-eventgraph

**EventGraph** is a development platform for high-level NLP applications in Japanese.
The core concept of EventGraph is event, a language information unit that is closely related to predicate-argument structure but more application-oriented.
Events are linked to each other based on their syntactic and semantic relations.

## Requirements

- Python 3.6
- pyknp: 0.4.1
- graphviz: 0.10.1

## Installation

```
$ python setup.py install
```

## Use EventGraph as a CLI application

### Constructing EventGraph

```
$ echo '彼女は海外勤務が長いので、英語がうまいに違いない。' | jumanpp | knp -tab | evg -o example-eventgraph.json
```

### Visualizing EventGraph

```
$ evgviz example-eventgraph.json example-eventgraph.svg
```

## Use EventGraph as a Python library

### Constructing EventGraph

```python
from pyknp_eventgraph import EventGraph
from pyknp_eventgraph.utils import read_knp_result_file

# construct EventGraph from a KNP result file
evg = EventGraph.build(read_knp_result_file('example.knp'))

# output EventGraph as a JSON file
evg.save('example-eventgraph.json')
```

### Loading EventGraph

```python
from pyknp_eventgraph import EventGraph

# load EventGraph from a JSON file
with open('example-eventgraph.json', encoding='utf-8', errors='ignore') as f:
    evg = EventGraph.load(f)
```

### Visualizing EventGraph

```python
from pyknp_eventgraph import EventGraph
from pyknp_eventgraph import make_image

# load EventGraph from a JSON file
with open('example-eventgraph.json', 'r', encoding='utf-8', errors='ignore') as f:
    evg = EventGraph.load(f)

# convert EventGraph to its visualization
make_image(evg, 'example-eventgraph.svg')
```

## Authors

- Kurohashi-Kawahara Lab, Kyoto University.
- contact@nlp.ist.i.kyoto-u.ac.jp
