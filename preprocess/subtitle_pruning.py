from turkish_normalization.utils import connect_database
from turkish_normalization.turkish_morph import morphological_analyzer
from pymongo import UpdateOne

def update_db(db, ids, words, poss):
    morph_results = morphological_analyzer(words, validate_only=True, hard_validate=False)
    update_commands = []
    for _id, (beg, end) in ids:
        local_words = words[beg:end]
        local_results = morph_results[beg:end]
        local_pos = poss[beg:end]
        result_dict = {}
        for w, r, p in zip(local_words, local_results, local_pos):
            result_dict[w] = {"pos": p, "is_valid": r}
        if not all(local_results):
            total_valid = False
        elif "SOFT" in local_results:
            total_valid = "SOFT"
        else:
            total_valid = True
        # tth += 0
        # print(_id, local_words)
        # print(_id, result_dict, total_valid)
        u = UpdateOne({"_id": _id}, {"$set": {"words": result_dict, "is_valid": total_valid}})
        update_commands.append(u)
    if update_commands:
        db.subtitles.bulk_write(update_commands)

db = connect_database("subtitle")
lines = db.subtitles.find({"is_valid": {"$exists": False}}, no_cursor_timeout=True, batch_size=10000)

ids = []
words = []
poss = []
offset = 0
for line in lines:
    current_words = list(line["words"])
    current_pos = list(line["words"].values())
    words.extend(current_words)
    ids.append((line["_id"], (offset, offset + len(current_words))))
    poss.extend(current_pos)
    offset += len(current_words)
    print("Current", line["_id"])
    if len(ids) == 10000:
        update_db(db, ids, words, poss)
        words = []
        ids = []
        poss = []
        offset = 0
update_db(db, ids, words, poss)

