#include "vm.h"

VM::VM(std::ifstream& source, bool interactive): file(source), interactive(interactive)
{
    // Get the file size
    file.seekg(0, std::ios::end);
    file_size = file.tellg();
    file.seekg(0, std::ios::beg);

    top_level_env = std::make_shared<ScmEnv>(nullptr);
    top_level_cont = std::shared_ptr<ScmCont>(nullptr);
    
    // Set the initial register values
    ENVT = top_level_env;
    CONT = top_level_cont;
    VALUE = std::shared_ptr<ScmObj>(nullptr);
    STACK = std::make_shared<scm_stack>();
    vm_init();
    init_constants();
}

void inline VM::read_byte(uint8_t* dest)
{
    file.read(reinterpret_cast<char*>(dest), 1);
    check_file();
}

void inline VM::read_4_bytes(uint32_t* dest)
{
    file.read(reinterpret_cast<char*>(dest), 4);
    check_file();
} 

void inline VM::read_double(double* dest)
{
    file.read(reinterpret_cast<char*>(dest), 8);
    check_file();
}

std::string VM::read_string()
{
    auto pos_backup = file.tellg();
    uint8_t byte_buffer;
    read_byte(&byte_buffer);
    auto len = 1;
    while(byte_buffer) {
        read_byte(&byte_buffer);
        len++;
    }
    
    if(len == 1) {
        return std::string();
    }
    
    char* buf = new char[len];
    file.seekg(pos_backup);
    check_file();
    file.read(buf, len);
    check_file();
    std::string new_str = std::string(buf);
    delete[] buf;
    return new_str;
}

void inline VM::check_file(void)
{
    if(!file) {
        std::cout << "File check failed, currently at position " << file.tellg() << std::endl;
        exit(1);
    }
}

void VM::run(void)
{
    if(interactive) {
        std::cout << "Cannot run() while in interactive mode" << std::endl;
        exit(1);
    }
    while(fetch_execute()) {
        //
    }
}

void VM::print_list(uint32_t uid)
{
    auto scm_pair = std::dynamic_pointer_cast<ScmPair>(constants[uid]);
    if(scm_pair == nullptr) {
        std::cout << "Dynamic pointer cast failed for ScmPair with uid " << uid << std::endl;
        return;
    }
    scm_pair->print();
    std::cout << std::endl;
}

void VM::init_constants(void)
{
    uint8_t code;
    read_byte(&code);
    if(code != OppCodes::data_start) {
        std::cout << "Data section does not start with a data_start OppCode" << std::endl;
    }

    read_byte(&code);
    while(code == OppCodes::const_data) {
        uint32_t uid;
        read_4_bytes(&uid);
        // std::cout << "UID is " << uid << std::endl;
        uint8_t type;
        read_byte(&type);
        if(type == Types::number) {
            // std::cout << "number" << std::endl;
            double val;
            read_double(&val);
            auto num = std::make_shared<ScmInt>(val);
            constants.insert(std::pair<uint32_t, std::shared_ptr<ScmObj> >(uid, num));
            std::cout << std::fixed << std::setprecision(7);
            // std::cout << "the double being read is " << val << std::endl;

        } else if(type == Types::string) {
            // std::cout << "string" << std::endl;
            std::string val = read_string();
            auto str = std::make_shared<ScmStr>(val);
            constants.insert(std::pair<uint32_t, std::shared_ptr<ScmObj> >(uid, str));
            // std::cout << "the string being read is " << val << std::endl;

        } else if(type == Types::symbol) {
            // std::cout << "symbol" << std::endl;
            std::string val = read_string();
            auto sym = std::make_shared<ScmSym>(val);
            constants.insert(std::pair<uint32_t, std::shared_ptr<ScmObj> >(uid, sym));
            // std::cout << "the symbol being read is " << val << std::endl;

        } else if(type == Types::list) {

            // std::cout << "list" << std::endl;
            uint32_t len_list;
            read_4_bytes(&len_list);
            // std::cout << "len of list is " << len_list << std::endl;
            // Read in the uid's
            auto list_uids = std::vector<uint32_t>();
            for(int i = 0; i < len_list; i++) {
                uint32_t uid;
                read_4_bytes(&uid);
                // std::cout << "list elem uid is " << uid << std::endl;
                list_uids.push_back(uid);
            }
            
            // Create the list object using ScmPair
            std::shared_ptr<ScmObj> cur = constants[Defaults::empty_list];
            for(int i = len_list - 1; i >= 0; i--) {
                cur = std::make_shared<ScmPair>(constants[list_uids[i]], cur);
            }
            constants[uid] = cur;
        } else {
            std::cout << "Of unknown type " << (unsigned int) type << " at pos " << (static_cast<int>(file.tellg()) - 1) << std::endl;
            exit(1);
        }
        read_byte(&code);
    }
    if(code != OppCodes::data_end) {
        std::cout << "Data section does not end with a data_end OppCode" << std::endl;
        exit(1);
    }
    // std::cout << "finished generating constants" << std::endl;
}

void VM::vm_init(void)
{
    for(uint8_t i = 1; i < BuiltInFunctions::not_built_in_last; i++) {
        std::string proc_name = built_in.find(static_cast<BuiltInFunctions>(i))->second;
        // std::shared_ptr<ScmObj> closure = std::static_pointer_cast<ScmObj>(std::make_shared<ScmClosure>(true, static_cast<BuiltInFunctions>(i), 0, top_lvl_environment));

        // I know these hold circular shared_pointers, but that is intended
        auto closure = std::make_shared<ScmClosure>(true, static_cast<BuiltInFunctions>(i), 0, top_level_env);
        top_level_env->map->insert(std::pair<std::string, std::shared_ptr<ScmObj> >(proc_name, closure));
    }
    constants = {
        std::pair<uint32_t, std::shared_ptr<ScmObj> >(Defaults::boolean_true, std::make_shared<ScmBool>(true)),
        std::pair<uint32_t, std::shared_ptr<ScmObj> >(Defaults::boolean_false, std::make_shared<ScmBool>(false)),
        std::pair<uint32_t, std::shared_ptr<ScmObj> >(Defaults::empty_list, std::make_shared<ScmPair>(nullptr, nullptr)),
    };
}

std::shared_ptr<ScmObj> VM::lookup_var(std::string var)
{
    std::shared_ptr<ScmEnv> cur = ENVT;
    while(cur != nullptr) {
        auto obj = cur->map->find(var);
        if (obj != cur->map->end()) {
            return obj->second;
        }
        cur = cur->prev;
    }
    return std::shared_ptr<ScmObj>(nullptr);
}

void VM::pop_continuation(void)
{
    if(CONT == nullptr) {
        std::cout << "Trying to pop an empty continuation chain" << std::endl;
        exit(1);
    }
    auto cur_cont = CONT;
    auto prev = CONT->prev;
    // !! Unsigned int to int converstion, may be lossy !!
    file.seekg(cur_cont->resume_loc);
    check_file();
    STACK = cur_cont->saved_stack;
    ENVT = cur_cont->env;
    CONT = prev;
}

void VM::push_continuation(uint32_t resume_loc)
{
    auto new_cont = std::make_shared<ScmCont>(resume_loc, ENVT, STACK, CONT);
    auto new_stack = std::make_shared<scm_stack>();
    STACK = new_stack;
    CONT = new_cont;
}

void VM::is_stack_size(int size, std::string func_name)
{
    if(STACK->size() != size) {
        std::cout << func_name << " takes only " << size << " no of arguments" << std::endl;
        std::cout << "stack size is " << STACK->size() << " instead" << std::endl;
        exit(1);
    }
}

bool VM::fetch_execute(void)
{
    uint8_t code;
    read_byte(&code);
    check_file();
    if(code == OppCodes::ext) {
        return false;
    } else if(code == OppCodes::opp_null) {
        // Nothing to do
    } else if (code == OppCodes::lookup) {
        auto var = read_string();
        check_file();
        auto val = lookup_var(var);
        if (val != nullptr) {
            VALUE = val;
        } else {
            std::cout << "Unbound variable " << var << std::endl;
            exit(1);
        }
    } else if (code == OppCodes::load_const) {
        uint32_t uid;
        read_4_bytes(&uid);
        check_file();
        auto iter = constants.find(uid);
        if (iter != constants.end()) {
            VALUE = iter->second;
        } else {
            std::cout << "Unbound constant with uid " << uid << std::endl;
            exit(1);
        }
    } else if (code == OppCodes::bind) {
        uint8_t no_vars;
        read_byte(&no_vars);
        check_file();
        
        // Create and set the new environment
        auto new_env = std::make_shared<ScmEnv>(ENVT);
        ENVT = new_env;
        for(auto i = 0; i < no_vars; i++) {
            auto var_str = read_string();
            check_file();
            if(!STACK->empty()) {
                std::shared_ptr<ScmObj> var_val = STACK->top();
                STACK->pop();
                ENVT->map->insert({var_str, var_val});
            } else {
                std::cout << "Error: empty stack while trying to bind variables" << std::endl;
                exit(1);
            }
        }
    } else if (code == OppCodes::apply) {
        std::shared_ptr<ScmClosure> closure = std::dynamic_pointer_cast<ScmClosure>(VALUE);
        if(closure == nullptr) {
            std::cout << "Trying to apply a non procedure" << std::endl;
            exit(1);
        }
        if(closure->built_in) {
            apply_builtin(closure);
        } else {
            ENVT = closure->closure_env;
            // !! This is a converstion from unsigned int to int, which might be lossy !!
            file.seekg(closure->porc_address);
            check_file();
        }
    } else if (code == OppCodes::ret) {
        pop_continuation();
    } else if (code == OppCodes::save_continuation) {
        uint32_t resume_address;
        read_4_bytes(&resume_address);
        push_continuation(resume_address);
    } else if (code == OppCodes::if_false_branch) {
        uint32_t branch_address;
        read_4_bytes(&branch_address);
        if(VALUE == constants[Defaults::boolean_false]) {
            file.seekg(branch_address);
            check_file();
        }
    } else if (code == OppCodes::if_true_branch) {
        uint32_t branch_address;
        read_4_bytes(&branch_address);
        if(VALUE != constants[Defaults::boolean_false]) {
            file.seekg(branch_address);
            check_file();
        }
    } else if (code == OppCodes::branch) {
        uint32_t branch_address;
        read_4_bytes(&branch_address);
        file.seekg(branch_address);
        check_file();
    } else if (code == OppCodes::push) {
        STACK->push(VALUE);
    } else if (code == OppCodes::make_closure) {
        uint32_t closure_address;
        read_4_bytes(&closure_address);
        auto new_closure = std::make_shared<ScmClosure>(false, BuiltInFunctions::not_built_in, closure_address, ENVT);
        VALUE = new_closure;
    } else if (code == OppCodes::set) {
        std::string var = read_string();
        std::shared_ptr<ScmEnv> cur = ENVT;
        bool found = false;
        while(cur != nullptr) {
            auto obj = cur->map->find(var);
            if (obj != cur->map->end()) {
                found = true;
                obj->second = VALUE;
            }
            cur = cur->prev;
        }
        if(!found) {
            std::cout << "Unable to set " << var << " could not find value" << std::endl;
            exit(1);
        }
    } else if (code == OppCodes::define) {
        std::string var = read_string();
        auto val = top_level_env->map->find(var);
        if(val != top_level_env->map->end()) {
            std::cout << "Unable to define " << var << " , value already exists" << std::endl;
            exit(1);
        } else {
            top_level_env->map->insert({var, VALUE});
        }
    } else if (code == OppCodes::label) {
        // Do nothing
    } else if (code == OppCodes::proc_end) {
        std::cout << "Reached proc end at " << (int) file.tellg() << std::endl;
        exit(1);
    } else if (code == OppCodes::data_start || code == OppCodes::data_end || code == OppCodes::const_data) {
        std::cout << "Const data instruction at " << (int) file.tellg() << std::endl;
        exit(1);
    } else if(code == OppCodes::unbind) {
        if(ENVT->prev == nullptr) {
            std::cout << "Trying to unbind at top level" << std::endl;
            exit(1);
        } else {
            ENVT = ENVT->prev;
        }
    } else {
        std::cout << "Unknown instruction " << (int) code << " At position " << std::hex << (int)(file.tellg()) << std::endl;
        exit(1);
    }
    return true;
}

int main(int argc, char** argv)
{
    if(argc < 2) {
        std::cout << "Usage: vm <compiled_file_name>" << std::endl;
        return -1;
    }
    std::ifstream file(argv[1], std::ios::binary);
    // std::ifstream file("/Users/khilansantoki/Desktop/Study/simplescm/build/compiled", std::ios::binary);
    if(!file) {
        std::cout << "Error opening file\n";
        return 1;
    }
    
    bool interactive = false;
    if(argc == 3) {
        if(std::string(argv[2]) == std::string("-i")) {
            interactive = true;
        }
    }
    
    VM virtual_machine = VM(file, interactive);

    if(!interactive) {
        virtual_machine.run();
        exit(0);
    } 

    using namespace ftxui;

    auto screen = ScreenInteractive::Fullscreen();
    auto renderer = Renderer([&] {
        return hbox({
            vbox({
                window(text("Registers") | color(Color::Blue), virtual_machine.draw_value_register()),
                window(text("StdIO"), virtual_machine.draw_current_out()),
                hbox({
                    window(text("Instructions") | color(Color::Red), virtual_machine.draw_instructions() | flex) | size(WIDTH, EQUAL, Terminal::Size().dimx / 4),
                    window(text("Stack") | color(Color::Green), virtual_machine.draw_stack()) | flex,
                }) | flex
            }) | size(WIDTH, EQUAL, Terminal::Size().dimx / 2) , 
            vbox({
                window(text("Current Environment") , virtual_machine.draw_environment() | flex),
                window(text("Previous Environment") , virtual_machine.draw_prev_environment()),
            }) | flex,
            virtual_machine.draw_conts(),
        });
    });

    // Handle space key press
    auto component = CatchEvent(renderer , [&](Event event) {
        if (event == Event::Character('q')) {
            screen.ExitLoopClosure()();
            return true;
        }
        if (event == Event::Character(' ')) {
            virtual_machine.clear_out();
            if(!virtual_machine.fetch_execute()) {
                screen.ExitLoopClosure()();
                return true;
            }
            screen.PostEvent(Event::Custom);  // Redraw UI
            return true;
        }
        return false;
    });

    screen.Loop(component);
    return 0;
}