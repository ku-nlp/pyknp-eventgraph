.. pyknp-eventgraph documentation master file, created by
   sphinx-quickstart on Thu Jun 11 16:40:29 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. role:: bash(code)
   :language: bash

====================================================================================
pyknp-eventgraph: A development platform for high-level NLP applications in Japanese
====================================================================================

About
=====

EventGraph_ is a development platform for high-level NLP applications in Japanese.
The core concept of EventGraph is event, a language information unit that is closely related to predicate-argument structure but more application-oriented.
Events are linked to each other based on their syntactic and semantic relations.

.. _EventGraph: https://github.com/ku-nlp/pyknp-eventgraph

Requirements
============

- Python 3.6 or later
- `pyknp`_
- `graphviz`_

.. _`pyknp`: https://github.com/ku-nlp/pyknp
.. _`graphviz`: https://github.com/xflr6/graphviz


Installation
============

To install pyknp-eventgraph, use :bash:`pip`.

.. code-block:: bash

   $ pip install pyknp-eventgraph

or

.. code-block:: bash

   $ git clone https://github.com/ku-nlp/pyknp-eventgraph.git
   $ cd pyknp-eventgraph
   $ python setup.py install [--prefix=path]

.. toctree::
   :maxdepth: 2
   :caption: References

   reference/index


Author/Contact
==============

Kurohashi-Kawahara Lab, Kyoto University (contact@nlp.ist.i.kyoto-u.ac.jp)

- Hirokazu Kiyomaru


.. toctree::
   :maxdepth: 1
   :caption: Other

   license


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
