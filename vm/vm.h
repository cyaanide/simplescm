#include "scheme_objects.h"

#include <ftxui/dom/elements.hpp>
#include <ftxui/dom/table.hpp>
#include <ftxui/screen/screen.hpp>
#include <ftxui/component/component.hpp>
#include <ftxui/component/screen_interactive.hpp>
#include <chrono>
#include <ctime>


class VM
{
    public:
    VM(std::ifstream& source, bool interactive);
    void run(void);
    
    void clear_out(void);
    bool fetch_execute(void);
    ftxui::Element draw_stack(void);
    ftxui::Element draw_stack(std::shared_ptr<scm_stack> stck);
    ftxui::Element draw_value_register(void);
    ftxui::Element draw_instructions(void);
    ftxui::Element draw_environment(void);
    ftxui::Element draw_prev_environment(void);
    ftxui::Element draw_current_out(void);
    ftxui::Element draw_conts(void);

    private:
    // VM Registers
    uint32_t IP = 0;
    std::shared_ptr<ScmObj> VALUE;
    std::shared_ptr<ScmEnv> ENVT;
    std::shared_ptr<ScmCont> CONT;
    std::shared_ptr<scm_stack> STACK;

    bool interactive;
    std::ifstream& file;
    std::streampos file_size;
    std::shared_ptr<ScmEnv> top_level_env;
    std::shared_ptr<ScmCont> top_level_cont;
    std::unordered_map<uint32_t, std::shared_ptr<ScmObj>> constants;
    std::string cur_out;

    void vm_init(void);
    void init_constants(void);
    void check_file(void);
    void read_byte(uint8_t* dest);
    void read_4_bytes(uint32_t* dest);
    void print_list(uint32_t uid);
    void read_double(double* dest);
    void pop_continuation(void);
    void push_continuation(uint32_t resume_loc);
    void is_stack_size(int size, std::string func_name);
    void apply_builtin(std::shared_ptr<ScmClosure> closure);

    std::string read_string();
    bool print_instruction(std::string& out);
    std::shared_ptr<ScmObj> lookup_var(std::string variable);

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
        std::pair<BuiltInFunctions, std::string>(BuiltInFunctions::display, "display"),
        std::pair<BuiltInFunctions, std::string>(BuiltInFunctions::num_equal, "="),
        std::pair<BuiltInFunctions, std::string>(BuiltInFunctions::num_greater, ">"),
        std::pair<BuiltInFunctions, std::string>(BuiltInFunctions::num_greater_equal, ">="),
        std::pair<BuiltInFunctions, std::string>(BuiltInFunctions::num_less, "<"),
        std::pair<BuiltInFunctions, std::string>(BuiltInFunctions::num_less_equal, "<="),
    };
};