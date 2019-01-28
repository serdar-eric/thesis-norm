from collections import defaultdict
from turkish_normalization.utils.turkish_sanitize import turkish_compare, turkish_lower
from turkish_normalization.utils import read_data, write_json


TWITTER_WORDS = "../data/u_twitter_words.txt"

turkish_chars = "abcçdefgğhıijklmnoöprsştuüvyzx"

vocab = read_data(TWITTER_WORDS)

groupped_words = defaultdict(dict)
not_groupped = set()
for word in vocab:
    initial = word[0]
    if initial == '_':
        continue
    chars_to_put_in = [c for c in turkish_chars if turkish_compare(initial, c)]
    # print('Word: %s -> %s' % (word, chars_to_put_in))
    # assert len(chars_to_put_in) != 0, word
    if not chars_to_put_in:
        not_groupped.add(initial)

    for c in chars_to_put_in:
        groupped_words[c][turkish_lower(word)] = {'original': word ,'count': vocab[word]}

print(not_groupped)

write_json("../data/twitter_words.txt", groupped_words)
