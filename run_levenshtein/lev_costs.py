import turkish_normalization.turkish_levenshtein as t_lev

insert_chars = ("aeoöğyr'h ", 0.1)
insert_high_vowels = ("ıiuüs", 0.2) # seperate them because they are usually use for suffixes
                                    # s for -aksın suffix
diacritic_subs = ([
    ("i", "ı"),
    ("u", "ü"),
    ("c", "ç"),
    ("g", "ğ"),
    ("o", "ö"),
    ("s", "ş"),
], 0)
substitute_chars = ([
    ("ı", "i"),
    ("e", "i"),
    ("i", "e"), # birlestiricem -> birleştireceğim | vericem -> vereceğim
    # ("ı", "a"), # anliyim -> anlayayım
    # ("i", "a"), # anlıyım -> anlayayım
    ("0", "o"),
    ("0", "ö"),
    ("q", "g"),
    ("q", "ğ"),
    ("q", "k"), # yoqq -> yok
    ("y", "ğ"), # deyişiyor -> değişiyor
    ("w", "v"), # yawrum -> yavrum
    ("u", "i"), # geleceğum -> geleceğim
    ("u", "ı"), # yavrım -> yavrum
    ("3", "e"), # güz3l -> güzel
    ("$", "ş"), # $arkı -> şarkı
    ("$", "s"), # herke$ -> herkes
    ("j", "c"), # abijim -> abicim
], 0.1)

substitute_chars_2 = ([
    ("h", "k"), # yok -> yoh
    ("v", "u"),
    ("z", "s"), # herkes -> herkez
], 0.8)

substitute_chars_3 = ([
    ("i", "a"), # aliyim -> alayım
    ("ı", "a"), # alıyım -> alayım
], 0.3)

substitute_cons_harm= ([
    ("p", "b"),
    ("ç", "c"),
    ("t", "d"), # ğ koymadım genellikle yanlış yazılmıyor
], 0.5 )

subtitute_for_adjacents = ([
    ("q", "w"),
    ("q", "a"),
    ("w", "q"),
    ("w", "e"),
    ("w", "s"),
    ("w", "a"),
    ("e", "w"),
    ("e", "s"),
    ("e", "d"),
    ("e", "r"),
    ("r", "e"),
    ("r", "d"),
    ("r", "f"),
    ("r", "t"),
    ("t", "r"),
    ("t", "f"),
    ("t", "g"),
    ("t", "y"),
    ("y", "t"),
    ("y", "g"),
    ("y", "h"),
    ("y", "u"),
    ("u", "y"),
    ("u", "h"),
    ("u", "j"),
    ("u", "ı"),
    ("ı", "u"),
    ("ı", "j"),
    ("ı", "k"),
    ("ı", "o"),
    ("o", "ı"),
    ("o", "k"),
    ("o", "l"),
    ("o", "p"),
    ("p", "o"),
    ("p", "l"),
    ("p", "ş"),
    ("p", "ğ"),
    ("ğ", "p"),
    ("ğ", "ş"),
    ("ğ", "i"),
    ("ğ", "ü"),
    ("ü", "ğ"),
    ("ü", "i"),
    ("a", "q"),
    ("a", "w"),
    ("a", "s"),
    ("a", "z"),
    ("s", "w"),
    ("s", "e"),
    ("s", "d"),
    ("s", "x"),
    ("s", "z"),
    ("s", "a"),
    ("d", "e"),
    ("d", "r"),
    ("d", "f"),
    ("d", "c"),
    ("d", "x"),
    ("d", "s"),
    ("f", "r"),
    ("f", "t"),
    ("f", "g"),
    ("f", "v"),
    ("f", "c"),
    ("f", "d"),
    ("g", "t"),
    ("g", "y"),
    ("g", "h"),
    ("g", "b"),
    ("g", "v"),
    ("g", "f"),
    ("h", "y"),
    ("h", "u"),
    ("h", "j"),
    ("h", "n"),
    ("h", "b"),
    ("h", "g"),
    ("j", "u"),
    ("j", "ı"),
    ("j", "k"),
    ("j", "m"),
    ("j", "n"),
    ("j", "h"),
    ("k", "ı"),
    ("k", "o"),
    ("k", "l"),
    ("k", "ö"),
    ("k", "m"),
    ("k", "j"),
    ("l", "o"),
    ("l", "p"),
    ("l", "ş"),
    ("l", "ç"),
    ("l", "ö"),
    ("l", "k"),
    ("ş", "p"),
    ("ş", "ğ"),
    ("ş", "i"),
    ("ş", "ç"),
    ("ş", "l"),
    ("i", "ğ"),
    ("i", "ü"),
    ("i", "ş"),
    ("z", "a"),
    ("z", "s"),
    ("z", "x"),
    ("x", "z"),
    ("x", "s"),
    ("x", "d"),
    ("x", "c"),
    ("c", "x"),
    ("c", "d"),
    ("c", "f"),
    ("c", "v"),
    ("v", "c"),
    ("v", "f"),
    ("v", "g"),
    ("v", "b"),
    ("b", "v"),
    ("b", "g"),
    ("b", "h"),
    ("b", "n"),
    ("n", "b"),
    ("n", "h"),
    ("n", "j"),
    ("n", "m"),
    ("m", "n"),
    ("m", "j"),
    ("m", "k"),
    ("m", "ö"),
    ("ö", "m"),
    ("ö", "k"),
    ("ö", "l"),
    ("ö", "ç"),
    ("ç", "ö"),
    ("ç", "l"),
    ("ç", "ş")
], 0.8)
delete_chars = ("ıi", 0.8) # sıtandart, tiren
delete_adjacent_chars = (list(subtitute_for_adjacents[0]), 1.0)

def get_costs():
    insert_costs = t_lev.initiliaze_costs(insert_chars, insert_high_vowels)
    substitute_costs = t_lev.initiliaze_costs(diacritic_subs, substitute_chars, substitute_chars_2, substitute_chars_3, substitute_cons_harm, subtitute_for_adjacents)
    delete_costs = t_lev.initiliaze_costs(delete_chars)
    delete_adjacent_costs = t_lev.initiliaze_costs(delete_adjacent_chars)
    return insert_costs, substitute_costs, delete_costs, delete_adjacent_costs

get_zero_array = t_lev.get_zero_array