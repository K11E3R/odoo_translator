"""Cache concurrency and atomic-write regression tests."""
from concurrent.futures import ThreadPoolExecutor

from po_translator.translator import TranslationCache


def test_concurrent_cache_writes_remain_valid_json(tmp_path):
    cache = TranslationCache(tmp_path / "cache.json")
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(lambda i: cache.set(f"source-{i}", f"target-{i}"), range(60)))
    reloaded = TranslationCache(tmp_path / "cache.json")
    assert reloaded.get("source-42") == "target-42"
    assert len(reloaded.cache) == 60
