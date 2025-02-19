from enum import Enum

class OppCodes(Enum):

    # Opp codes for instructions
    opp_null = 0
    lookup = 1
    load_const = 2
    bind = 3
    apply = 4
    ret = 5
    save_cont = 6
    if_false_branch = 7
    if_true_branch = 8
    branch = 9
    push = 10
    make_closure = 11
    set = 12
    define = 13
    ext = 14

    # Opp codes for types of constants
    defaults_start = 15
    defaults_end = 16
    boolean = 17
    string = 18
    number = 19
    list = 20
    symbol = 21
    label = 22

    