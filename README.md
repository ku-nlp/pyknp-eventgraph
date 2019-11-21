# pyknp-eventgraph

**EventGraph** is a Python library for event-level text processing.
In EventGraph, an **event** is defined by a predicate-argument structure (PAS) and the associated information such as the modality and tense.
Events are linked based on their grammatical and semantic relations.

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

# convert knp results to the eventgraph
evg = EventGraph.build(read_knp_result_file('example.knp'), verbose=True)
# output the eventgraph as a JSON file
evg.output_json('example-eventgraph.json')
```

### Loading EventGraph

```python
import json
from pyknp_eventgraph import EventGraph

# load the eventgraph from a JSON file
with open('example-eventgraph.json', encoding='utf-8', errors='ignore') as f:
    evg = EventGraph.load(json.load(f), verbose=True)
```

### Visualizing EventGraph

```python
import json
from pyknp_eventgraph import EventGraph, EventGraphVisualizer

with open('example-eventgraph.json', 'r', encoding='utf-8', errors='ignore') as f:
    evg = EventGraph.load(json.load(f), verbose=True)

# prepare a visualizer
evgviz = EventGraphVisualizer()
# convert a eventgraph to its visualization
evgviz.make_image(evg, 'example-eventgraph.svg', verbose=True)
```

## Authors

- Kurohashi-Kawahara Lab, Kyoto University.
- contact@nlp.ist.i.kyoto-u.ac.jp
