# contaix.aggregation

Tools for aggregating contexts

### Functions

| [`aggregate_store`](#contaix.aggregation.aggregate_store)(store, \*[, ...])   | Aggregates and processes text files from a store.   |
|--------------------------------------------------------------------------------------|-----------------------------------------------------|

### contaix.aggregation.aggregate_store(store, , min_number_of_duplicated_lines=None, max_num_characters=None, exclude=None, chk_size=None, egress=None, \*\*store_aggregate_kwargs)

Aggregates and processes text files from a store.

* **Parameters:**
  * **store** ([`Mapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping)) – The source store (e.g., TextFiles instance)
  * **min_number_of_duplicated_lines** ([`int`](https://docs.python.org/3/builtins/functions.html#int) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – If not None, minimum block size for deduplication.
  * **max_num_characters** ([`int`](https://docs.python.org/3/builtins/functions.html#int) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Maximum number of characters per file.
  * **exclude** ([`Iterable`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Iterable) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Set of filenames to exclude.
  * **chk_size** ([*int*](https://docs.python.org/3/builtins/functions.html#int)) – Chunk size for aggregation. If None, won’t chunk
  * **egress** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`Callable`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Callable) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Template for output filenames or function to call on each chunk
  * **\*\*store_aggregate_kwargs** – Additional keyword arguments to pass to store_aggregate.
