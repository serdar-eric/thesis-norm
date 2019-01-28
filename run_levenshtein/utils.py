from pathlib import Path
from multiprocessing import Lock

def create_folder(*path):
    path = Path(*path).resolve()
    try:
        path.mkdir()
    except FileExistsError:
        pass


def write_data(filename, data):
    with open(filename, "w") as fp:
        for r, c, w in data:
            fp.write("%.2f %s - %d\n" % (r, w, c))

def write_plain(filename, data):
    with open(filename, "w") as fp:
        fp.write("\n".join(data))