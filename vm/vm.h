#include <fstream>
#include "scheme_objects.h"


class VM
{
    public:
    VM(std::ifstream& source);
    void run(void);
    
    private:
    uint32_t pos = 0;
    std::ifstream& file;
    std::streampos file_size;
    std::shared_ptr<environment> top_lvl_environment;
    std::unordered_map<uint32_t, std::shared_ptr<ScmObj>> constants;
    // update this to use the constexpr vectory or array
    std::unordered_map<BuiltInFunctions, std::string> built_in {
        std::pair<BuiltInFunctions, std::string>(BuiltInFunctions::addition, "+"),
        std::pair<BuiltInFunctions, std::string>(BuiltInFunctions::subtraction, "-"),
        std::pair<BuiltInFunctions, std::string>(BuiltInFunctions::division, "/"),
        std::pair<BuiltInFunctions, std::string>(BuiltInFunctions::multiplication, "*"),
        std::pair<BuiltInFunctions, std::string>(BuiltInFunctions::cons, "cons"),
        std::pair<BuiltInFunctions, std::string>(BuiltInFunctions::car, "car"),
        std::pair<BuiltInFunctions, std::string>(BuiltInFunctions::cdr, "cdr"),
        std::pair<BuiltInFunctions, std::string>(BuiltInFunctions::is_number, "number?"),
        std::pair<BuiltInFunctions, std::string>(BuiltInFunctions::is_string, "string?"),
        std::pair<BuiltInFunctions, std::string>(BuiltInFunctions::is_pair, "pair?"),
        std::pair<BuiltInFunctions, std::string>(BuiltInFunctions::is_symbol, "symbol?"),
        std::pair<BuiltInFunctions, std::string>(BuiltInFunctions::eq, "eq?"),
        std::pair<BuiltInFunctions, std::string>(BuiltInFunctions::equal, "equal?"),
    };
    void vm_init(void);
    void init_constants(void);
    void check_file(void);
    void read_byte(uint8_t* dest);
    void read_4_bytes(uint32_t* dest);
    void read_double(double* dest);
    std::string read_string();
    void print_list(uint32_t uid);
};