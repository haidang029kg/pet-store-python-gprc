from typing import List


def chunk_size_splitter(chunk_size: int, number_value: int) -> List[int]:
    if number_value < chunk_size:
        return [number_value]

    left_part = int(number_value / chunk_size)
    right_part = number_value % chunk_size
    res = [chunk_size] * left_part
    if right_part:
        res.append(right_part)
    return res
