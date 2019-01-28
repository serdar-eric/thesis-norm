import re
import os

main_path = "./data/OpenSubtitles2018/raw/tr"


def list_dir(c_dir):
    for subdir in os.listdir(c_dir):
        yield subdir, os.path.join(c_dir, subdir)


pattern = re.compile(
    r"<s.*?>(?:\s*<time.*?/>)?\s*(.+?)(?:\s*<time.*?/>)?\s*</s>",
    re.MULTILINE | re.DOTALL,
)
with open("./data/subtitle_merged.txt", "w") as sb:
    count = 0
    sentences = []
    for year, y_dir_path in list_dir(main_path):
        for s_id, s_dir_path in list_dir(y_dir_path):
            for s_file, f_dir_path in list_dir(s_dir_path):
                print("Working on %d) %s - %s - %s" % (year, s_id, s_file))
                count += 1
                sentences += ["<<<<<%s - %s - %s>>>>>" % (year, s_id, s_file)]

                with open(f_dir_path) as fp:
                    content = fp.read()
                    sentences += pattern.findall(content)

                if count % 10000 == 0:
                    sb.write("\n".join(sentences))
                    # sb.flush()
                    print("Flushed!!!")
                    del sentences
                    sentences = []
                    count = 0
