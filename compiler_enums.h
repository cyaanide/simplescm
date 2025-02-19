#include <cstdint>

enum OpCodes: std::uint8_t
{
    opp_null = 0,
    lookup = 1,
    load_const = 2,
    bind = 3,
    apply = 4,
    ret = 5,
    save_continuation = 6,
    if_false_branch = 7,
    if_true_branch = 8,
    branch = 9,
    push = 10,
    make_closure = 11,
    set = 12,
    define = 13,
    ext = 14,
    data_start = 15,
    data_end = 16,
    label = 17,
};

enum Types: std::uint8_t
{
    boolean = 1,
    string = 2,
    number = 3,
    list = 4,
    symbol = 5,
};

enum Defaults: std::uint8_t
{
    boolean_false = 1,
    boolean_true = 2,
    empty_list = 3,
};