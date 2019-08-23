import SequenceAlignment






if __name__ == "__main__":
    s1 = 'ABCDEFGHIJKLMNOP'
    s2 = 'BCEFKHJ'
    aligned = SequenceAlignment.get_alignment(s1, s2)
    print(aligned['match_starts_in_1'], aligned['match_ends_in_1'])

    print(s1, "[", s1[aligned['match_starts_in_1']:aligned['match_ends_in_1'] + 1], "]")
    print(s2)
    print(aligned['result_1'])
    print(aligned['result_2'])

# I'm thinking that a tweaked version of the dynamic programming string alignment routine is
# the best way to identify the correct alignment of the two strings.





