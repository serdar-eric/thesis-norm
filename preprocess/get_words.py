import redis
import pickle

from turkish_normalization.utils import connect_database
from turkish_normalization.utils.turkish_sanitize import turkish_lower, turkish_sanitize, turkish_lcase

rds = redis.Redis(db=0)
db = connect_database("twitter")
tweets = db.tweets_tokenized.find(
    {}, {"entities.words"}, no_cursor_timeout=True, batch_size=1000
)
pipe = rds.pipeline()
count = 0
for tweet in tweets:
    tweet_id = tweet["_id"]
    words = tweet["entities"]["words"]
    print("Count: %d, Processing: %s" % (count, tweet_id))
    count += 1
    collect = []
    for word in words:
        beg, end = word["indices"]
        word = word["value"]
        if len(word) < 2:
            rds.sadd("eliminated_words", word)
            continue
        if turkish_sanitize(word[0]) not in turkish_lcase:
            rds.rpush("not_turkish", pickle.dumps((word[0], word, tweet_id)))
        initial = turkish_sanitize(word[0])
        word = turkish_lower(word)
        pipe.sadd("initials", initial)
        ret = pipe.sadd("i:%s:w" % initial, word)
        # if ret:
        #     pipe.incr("i:%s:c" % initial)
        #     pipe.incr("unique:count")
        pipe.incr("total:count")
        pipe.incr("w:%s:c" % word)
        pipe.rpush("w:%s:p" % word, pickle.dumps((tweet_id, beg)))
    if count % 20000 == 0:
        pipe.execute()
    # if count % 100000 == 0:
    #         # pprint(word_set)
    #     # input()
    #     break

pipe.execute()
rds.save()
tweets.close()
