import re

HYPENS = "-–"
punct = ".?!\""
extract_pattern = re.compile(r"(?:[-–]\s*)?(.+?)(?:\n)", re.DOTALL)

with open("./data/subtitle_merged.txt") as frp, open("./data/subtitle_merged_corrected.txt", "w") as fwp:
    count = 0
    sentences = []
    save = []
    cont = False
    might_cont = False
    for line in frp:
        count += 1
        try:
            line = extract_pattern.findall(line)[0].strip()
        except:
            continue
        if line.startswith("<<<<<"):
            sentences.append(line)
            continue
        beg_incomplete = line.startswith("...") or line.startswith("..")   
        end_incomplete = line.endswith("...") or line.endswith("..")
        beg, end = (
         (
          3 if line.startswith("...") else
          2 if line.startswith("..") else
          0
         ), 
         (
          -3 if line.endswith("...") else
          -2 if line.endswith("..") else
           len(line))
         )
        if not end_incomplete:
            if might_cont:
                if beg_incomplete and not end_incomplete:
                    save.append(line[beg:end])
                elif not str.isupper(line[0]):
                    save.append(line)
                else:
                    save[-1] = save[-1] + "..."
                    sentences.append(line)
            elif cont: 
                if not str.isupper(line[0]) or save[-1][-1] in ":;":
                    save.append(line)
                else:
                    sentences.append(line)

        if end_incomplete:
            might_cont = True
            save.append(line[beg:end])
        elif line[-1] not in punct:
            cont = True
            save.append(line[beg:end])
        else:
            might_cont = False
            cont = False
            if save:
                sentences.append(" ".join(save))
                save = []
            else:
                sentences.append(line)
        if count % 100000 == 0:
            fwp.write("\n".join(sentences))
            del sentences
            sentences = []