import re
import json
import redis
import pickle

from collections import defaultdict
from turkish_normalization.utils.turkish_sanitize import turkish_lower, turkish_sanitize
from turkish_normalization.utils import connect_database

subtitle_path = "../../data/subtitle_merged_corrected.txt"
ALPHA = "[^\W\d_]"
token_specifications = [
    ("NUMBER", r"\d+(\.\d*)?"),
    ("WORD", r"[^\W\d_]+(\'[^\W\d_]+)?"),
    ("MISMATCH", r"\S+"),
]
rds = redis.Redis(db=1)
word_set = defaultdict(dict)
pattern_str = "|".join("(?P<%s>%s)" % pair for pair in token_specifications)
tok_pattern = re.compile(pattern_str)
word_count = 0
pipe = rds.pipeline()
with open(subtitle_path, "r") as fp:
    current = 0
    global_offset = 0
    for line in fp:
        current += 1
        print("Line %d" % current)
        if line.startswith("<<<<<"):
            continue
        words = defaultdict(list)
        for mo in tok_pattern.finditer(line):
            kind = mo.lastgroup
            value = mo.group()
            beg, end = mo.span()
            if kind == "WORD":
                if len(value) < 2:
                    continue
                words[value].append((beg, end))
                word = turkish_lower(value)
                initial = turkish_sanitize(word[0])
                pipe.sadd("initials", initial)
                ret = pipe.sadd("i:%s:w" % initial, word)
                # if ret:
                #     pipe.incr("i:%s:c" % initial)
                #     pipe.incr("unique:count")
                pipe.incr("total:count")
                pipe.incr("w:%s:c" % word)
                pipe.rpush("w:%s:p" % word, pickle.dumps((current, beg)))
        if current % 20000 == 0:
            # execute pipeline every 100000 iteration
            pipe.execute()
        # if current % 1000000 == 0:
        #     # pprint(word_set)
        #     break
pipe.execute()
rds.save()
