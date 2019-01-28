from turkish_normalization.utils import read_data, get_config
from turkish_normalization.database_wrappers import WordDB
from pathlib import Path

rds = get_config(str(Path(__file__).with_name("redis.toml")))

def get_counts(words, pipe):
    counts = []
    for w in words:
        pipe.get("w:%s:c" % w)
        if len(pipe) == 10000:
            c = pipe.execute()
            counts.extend(c)
    counts.extend(pipe.execute())
    counts = {w:int(c) for w, c in zip(words, counts)}
    return counts


def get_target():
    return JsonWrapper(str(Path(__file__).with_name("samples.json")))


# def get_target():
#     rds = get_config("redis.toml")
#     subtitle_words = WordDB(**rds.subtitle)
#     return subtitle_words.initials

def get_source():
    twitter_words = WordDB(**rds.twitter)
    return twitter_words.initials

def get_source_word_counts(words):
    twitter_words = WordDB(**rds.twitter)
    rds = twitter_words.get_rds_instance()
    pipe = rds.pipeline()
    return get_counts(words, pipe)


class JsonWrapper:
    def __init__(self, filepath):
        self._data = read_data(filepath)
    
    def count(self, initial):
        return len(self._data.get(initial, []))
    
    def __getitem__(self, initial):
        return self._data[initial]
    
    def get(self, initial, default):
        res = self.__getitem__(initial)
        return res if res else default
    
    def get_range(self, initial, beg, end):
        res = self.__getitem__(initial)
        return res[beg:end]