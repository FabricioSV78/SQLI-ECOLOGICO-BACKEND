def count_lines_of_code(path: str) -> int:
    with open(path, "r", encoding="utf-8") as f:
        return sum(1 for _ in f)

def is_java_file(filename: str) -> bool:
    return filename.endswith(".java")
