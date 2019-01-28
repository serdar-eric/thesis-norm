import cProfile
import logging
import logging.handlers
import multiprocessing as mp
import string
import time
from operator import itemgetter
from timeit import default_timer as timer

from turkish_normalization.utils.turkish_sanitize import turkishify
import turkish_normalization.turkish_levenshtein as t_lev
from data import get_source, get_source_word_counts, get_target
from lev_costs import get_costs, get_zero_array
from utils import create_folder, write_data, write_plain

BASE_FOLDER = "results"
MODEL_NAME = "multi_deneme"
TIME_STR = time.strftime("%Y-%m-%d_%H:%M:%S", time.localtime())

_logger = logging.getLogger(__name__)

def name_filter(record):
    name = mp.current_process().name
    if isinstance(name, str):
        fmt = "%9s" % name
    else:
        fmt = "Process %d" % name
    record.p_name = fmt
    return True


def setup_logging():
    formatter_no_time = logging.Formatter(fmt="%(p_name)s | %(message)s")
    formatter_with_time = logging.Formatter(fmt="%(asctime)s - %(p_name)s | %(message)s")
    create_folder("logs", MODEL_NAME)
    log_queue = mp.Queue(-1)
    queue_handler = logging.handlers.QueueHandler(log_queue)
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter_no_time)
    file_handler = logging.FileHandler(
        "./logs/%s/%s_%s.log" % (MODEL_NAME, MODEL_NAME, TIME_STR)
    )
    file_handler.setFormatter(formatter_with_time)
    file_handler.setLevel(logging.DEBUG)

    _logger.addHandler(queue_handler)
    _logger.setLevel(logging.DEBUG)
    queue_listener = logging.handlers.QueueListener(
        log_queue, stream_handler, file_handler
    )
    _logger.addFilter(name_filter)
    queue_listener.start()
    return log_queue


def process_divider(counts, ps_num):
    pool = [[] for _ in range(ps_num)]
    last_proc = 0
    for initial, _, _, comparison in counts:
        each_proc_comp = comparison // ps_num
        left_over_comp = comparison % ps_num
        offset = 0
        for p in pool:
            p.append((initial, (offset, offset + each_proc_comp)))
            offset += each_proc_comp

        if left_over_comp != 0:
            pool[last_proc].append((initial, (comparison - left_over_comp, comparison)))
            last_proc += 1
            last_proc %= ps_num
        # pool[-1].append((initial, (offset, comparison)))
    return pool


def calculate_comparisons(_source, _target):
    counts = []
    total_target = 0
    total_comparison = 0
    for initial in string.ascii_lowercase:
        source_word_counts = _source.count(initial)
        target_word_counts = _target.count(initial)
        if source_word_counts == 0 or target_word_counts == 0:
            continue
        current_comparisons = source_word_counts * target_word_counts
        counts.append(
            (initial, current_comparisons, source_word_counts, target_word_counts)
        )
        total_target += target_word_counts
        total_comparison += current_comparisons
    counts = sorted(counts, key=itemgetter(1), reverse=True)
    return counts


def write_result(initial, word, results):
    create_folder(BASE_FOLDER, MODEL_NAME, TIME_STR, initial)
    processed_results = sorted(results, key=lambda k: (k[0], -k[1]))
    write_data(
        f"./{BASE_FOLDER}/{MODEL_NAME}/{TIME_STR}/{initial}/{word}.txt",
        processed_results,
    )


def write_cache(result_cache):
    for i, w, p in result_cache:
        write_result(i, w, p)


def fill_cache(_source, initial, cache):
    # only consider the request if cache missed
    if initial not in cache:
        _logger.debug("Cache missed | Initial %s", initial)
        load_time = timer()
        res = _source.get(initial, [])
        new_res = []
        for w in res:
            turk_w = turkishify(w)
            if turk_w != -1:
                new_res.append((w, t_lev.tur_enc(turk_w)))
        cache[initial] = new_res
        _logger.debug("Cache filled | Initial %s | Took %.2f", initial, timer() - load_time)
    else:
        _logger.debug("Cache hit | Initial %s", initial)

def word_lookup(reader, _source, cache, locks, schedules):
    _source = get_source()
    last_recieved_places = {}
    updated = False
    while True:
        if reader.poll(0.001):
            # if there is anything to read, serve for masters
            _id, initial = reader.recv()
            if _id == -1:
                break
            _logger.info("Recieved => Sender ID: %d, Initial: %s", _id, initial)
            fill_cache(_source, initial, cache)
            # let's release the waiting processes
            lock = locks[_id]
            with lock:
                lock.notify()
            last_p = last_recieved_places.get(_id, 0)
            last_recieved_places[_id] = last_p + 1
            updated = True
        elif updated:
            # if there is nothing to do, just fill cache according to schedules
            _logger.debug("Updating Cache")
            updated = False
            # for _id, last_p in last_recieved_places.items():
            #     next_initial, _ = schedules[_id][last_p]
            #     _logger.info("Cache pre-filling => Process %d | Initial %s ", _id, next_initial)
            #     fill_cache(_source, next_initial, cache)
            #     _logger.info("Cache pre-filled => Process %d | Initial %s ", _id, next_initial)
        else:
            pass
            #_logger.debug("Cached    | Doing nothing")



def get_source_words(initial, cache, sender, lock):
    if initial not in cache:
        _logger.debug("Cache missed | Initial %s", initial)
        _id = int(mp.current_process().name) - 1
        sender.send((_id, initial))
        with lock:
            lock.wait()
    else:
        _logger.debug("Cache Hit | Initial %s", initial)
    return cache[initial]


def run_levenshtein(targets, _source, _target, cache, sender, lock):
    # insert_costs, substitute_costs, delete_costs, delete_adjacent_costs = get_costs()
    t_lev.set_costs(*get_costs(), delete_repeating_costs=get_zero_array())
    comparison_count = 0
    total_start = timer()
    current_initial = 0
    for initial, (beg, end) in targets:
        data_start = timer()
        # source_words = _source.get(initial, [])
        source_words = get_source_words(initial, cache, sender, lock)
        data_end = timer()
        target_words = _target.get_range(initial, beg, end)
        # source_word_counts = get_source_word_counts(source_initial_words)
        current_initial += 1
        _logger.info(
            "BEGIN | Initial: %s (%2d/%2d) | Took %.2f to load",
            initial,
            current_initial,
            len(targets),
            data_end - data_start,
        )
        initial_start = timer()
        initial_comparison_count = 0
        target_count = 1
        result_cache = []
        # TODO: kelime eylem olabiliyorsa r harfinin düşmesi daha düşük olsun diğer türlü olmasın
        # artık -> atttık
        for w in target_words:            
            results = t_lev.turkish_levenshtein(
                source_words,
                t_lev.tur_enc(w),
                threshold=2.0,
            )
            processed_results = []
            target_comparison = 0
            target_start = timer()
            for dist, word in results:
                # _logger.debug("Process %d | Comparing %s <=> %s | Result %d", _id, w, word, dist)
                if dist < 0:
                    continue
                comparison_count += 1
                target_comparison += 1
                initial_comparison_count += 1
                count = 1  # source_word_counts[word]
                processed_results.append((dist, count, word))
            target_end = timer()
            _logger.info(
                "Processing: %25s (%2d/%2d) | Took %5.2fs | %5d comparisons",
                w,
                target_count,
                len(target_words),
                target_end - target_start,
                target_comparison,
            )
            target_count += 1
            result_cache.append((initial, w, processed_results))
            # TODO: async olacak
            if len(result_cache) == 10:
                write_beg = timer()
                write_cache(result_cache)
                result_cache = []
                write_end = timer()
                _logger.debug(
                    "Results are dumped | Took %.2f",
                    write_end - write_beg,
                )
        write_cache(result_cache)
        initial_end = timer()
        _logger.info(
            "END | Initial %s | Took %5.2fs | %d comparisons",
            initial,
            initial_end - initial_start,
            initial_comparison_count,
        )
    total_end = timer()
    _logger.info(
        "Took totally %.2fs | %d comparisons",
        total_end - total_start,
        comparison_count,
    )


def process_profiler(targets, _source, _target, cache, sender, lock):
    create_folder("profiles", MODEL_NAME)
    create_folder("profiles", MODEL_NAME, TIME_STR)
    profiling_result_file = "./profiles/%s/%s/process%d.cprof" % (
        MODEL_NAME,
        TIME_STR,
        _id,
    )

    cProfile.runctx(
        "run_levenshtein(targets, _source, _target, cache, sender, lock)",
        globals(),
        locals(),
        profiling_result_file,
    )


def main():
    # TODO: make argument parser
    create_folder(BASE_FOLDER)
    create_folder(BASE_FOLDER, MODEL_NAME)
    create_folder(BASE_FOLDER, MODEL_NAME, TIME_STR)
    log_queue = setup_logging()
    PS_NUM = 7
    insert_costs, substitute_costs, delete_costs, delete_adjacent_costs = get_costs()
    _source = get_source()
    _target = get_target()
    mng = mp.Manager()
    cache = mng.dict()

    locks = [mng.Condition() for _ in range(PS_NUM)]
    reader, writer = mp.Pipe()
    counts = calculate_comparisons(_source, _target)
    pool = process_divider(counts, PS_NUM)
    processes = [
        mp.Process(
            target=run_levenshtein,
            args=(targets, _source, _target, cache, writer, locks[_id-1]),
            name=_id,
        )
        for _id, targets in enumerate(pool, start=1)
    ]
    all_beg = timer()
    listener = mp.Process(target=word_lookup, args=(reader, _source, cache, locks, pool), name="Cacher")
    listener.start()
    for p in processes:
        p.start()
    for p in processes:
        p.join()
    all_end = timer()
    _logger.info(
        "Whole processed took %.2fs with %d processes", all_end - all_beg, PS_NUM
    )
    _logger.info("Run ID: %s", TIME_STR)
    writer.send((-1, None))
    listener.join()

if __name__ == "__main__":
    main()
