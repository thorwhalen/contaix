"""Tools for aggregating contexts"""

from typing import Optional, Mapping, Iterable, Union, Callable
from dol import TextFiles, filt_iter, wrap_kvs, Pipe, store_aggregate
from contaix.util import identity


def aggregate_store(
    store: Mapping,
    *,
    min_number_of_duplicated_lines: Optional[int] = None,
    max_num_characters: Optional[int] = None,
    exclude: Optional[Iterable] = None,
    chk_size=None,
    egress: Optional[Union[str, Callable]] = None,
    **store_aggregate_kwargs,
):
    """
    Aggregates and processes text files from a store.

    Parameters:
        store: The source store (e.g., TextFiles instance)
        min_number_of_duplicated_lines (int): If not None, minimum block size for deduplication.
        max_num_characters (int): Maximum number of characters per file.
        exclude (set): Set of filenames to exclude.
        chk_size (int): Chunk size for aggregation. If None, won't chunk
        egress (str or callable): Template for output filenames or function to call on each chunk
        **store_aggregate_kwargs: Additional keyword arguments to pass to store_aggregate.
    """
    if exclude is None:
        exclude = set()

    wrappers = []

    if exclude is not None:
        wrappers.append(filt_iter(filt=lambda x: x not in exclude))

    if min_number_of_duplicated_lines is not None:
        from hg import deduplicate_string_lines

        remove_duplicate_lines = wrap_kvs(
            value_decoder=lambda v: deduplicate_string_lines(
                v,
                min_block_size=min_number_of_duplicated_lines,
                return_removed_blocks=False,
            )
        )
    else:
        remove_duplicate_lines = identity

    if max_num_characters is not None:
        wrappers.append(wrap_kvs(value_decoder=lambda v: v[:max_num_characters]))

    capped_num_characters = wrap_kvs(value_decoder=lambda v: v[:max_num_characters])

    if len(wrappers) > 0:
        store_wrap = Pipe(
            filt_iter(filt=lambda x: x.endswith(".md") and x not in exclude),
            remove_duplicate_lines,
            capped_num_characters,
        )
    else:
        store_wrap = identity

    wrapped_store = store_wrap(store)

    if isinstance(egress, str):
        output_template = egress
        egress = output_template.format
    else:
        assert egress is None or callable(
            egress
        ), "egress must be None, str, or callable"

    if isinstance(chk_size, int):
        from lkj.chunking import chunk_iterable

        chunks = chunk_iterable(wrapped_store, chk_size)
        if egress is not None:
            egress = "store_aggregate_{:02.0f}.md"
        for i, sub_store in enumerate(chunks, 1):
            store_aggregate(sub_store, egress=egress(i), **store_aggregate_kwargs)
    else:
        if egress is None:
            egress = identity
        return store_aggregate(wrapped_store, egress=egress, **store_aggregate_kwargs)
