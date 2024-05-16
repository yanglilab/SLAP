def read_txt_line(file_path):
    item_list = []
    with open(file_path, "r") as f:
        for line in f:
            line = line.strip("\n")
            item_list.append(line)

        f.close()
    return item_list