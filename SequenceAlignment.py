
def element_penalty(elem_1, elem_2, penalty_diff=7, weighted_diff=False):
    penalty = 0
    if elem_1 != elem_2:
        if weighted_diff:
            mismatch = 0
            depth = min(len(elem_1), len(elem_2))
            for idx in range(depth):
                if elem_1[idx] != elem_2[idx]:
                    mismatch += 1
            penalty = int(penalty_diff * (mismatch / depth))
        else:
            penalty = penalty_diff
    return penalty



def build_alignment_matrix(seq_1, seq_2, penalty_blank=2, penalty_blank_other=13, penalty_diff=7, weighted_diff=False):
    len_1 = len(seq_1)
    len_2 = len(seq_2)

    answer = []
    for x in range(len_1 + 1):
        for y in range(len_2 + 1):
            if x == 0:
                row = [y * penalty_blank]
                answer.append(row)
            else:
                row = answer[y]
                if y == 0:
                    row.append(x * penalty_blank)
                else:
                    p = [element_penalty(seq_1[x - 1], seq_2[y - 1], penalty_diff, weighted_diff) + answer[y - 1][x - 1],
                         penalty_blank + answer[y - 1][x],
                         (penalty_blank if y >= len_2 else penalty_blank_other) + answer[y][x - 1]]
                    row.append(min(p))
    return answer


def get_alignment_score(seq_1, seq_2, penalty_blank=2, penalty_blank_other=13, penalty_diff=7, weighted_diff=False):
    alignment_matrix = build_alignment_matrix(seq_1, seq_2, penalty_blank, penalty_blank_other, penalty_diff, weighted_diff)
    return alignment_matrix[-1][-1]

def get_alignment(seq_1, seq_2, penalty_blank=2, penalty_blank_other=7, penalty_diff=5, weighted_diff=False):
    alignment_matrix = build_alignment_matrix(seq_1, seq_2, penalty_blank, penalty_blank_other=penalty_blank_other,
                                              penalty_diff=penalty_diff, weighted_diff=weighted_diff)
    x = len(seq_1)
    y = len(seq_2)
    aseq1 = []
    aseq2 = []
    sub_seq_1_begin = x + 1
    sub_seq_1_end = -1


    while x > 0 or y > 0:

        if x > 0 and y > 0 \
                and alignment_matrix[y][x] == alignment_matrix[y - 1][x - 1] \
                        + element_penalty(seq_1[x - 1], seq_2[y - 1], penalty_diff=penalty_diff, weighted_diff=weighted_diff):
            aseq1.insert(0, seq_1[x - 1])
            aseq2.insert(0, seq_2[y - 1])
            if seq_1[x - 1].isalnum():
                sub_seq_1_end = max(x - 1, sub_seq_1_end)
                sub_seq_1_begin = min(x - 1, sub_seq_1_begin)
            x -= 1
            y -= 1
        elif y > 0 and alignment_matrix[y - 1][x] + penalty_blank == alignment_matrix[y][x]:
            aseq1.insert(0, "-")
            aseq2.insert(0, seq_2[y - 1])
            y -= 1
        elif x > 0 and alignment_matrix[y][x - 1] + (penalty_blank if y in [0, len(seq_2)] else penalty_blank_other) == alignment_matrix[y][x]:
            aseq1.insert(0, seq_1[x - 1])
            aseq2.insert(0, "-")
            x -= 1

    alignment = {
        'score': alignment_matrix[-1][-1],
        'result_1': aseq1,
        'result_2': aseq2,
        'match_starts_in_1': sub_seq_1_begin,
        'match_ends_in_1': sub_seq_1_end

    }
    return alignment




