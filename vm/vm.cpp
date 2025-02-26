#include "vm.h"

VM::VM(std::ifstream& source): file(source)
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
    vm_init();
    init_constants();
    fetch_execute();
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
        std::pair<uint32_t, std::shared_ptr<ScmObj> >(Defaults::boolean_true, std::make_shared<ScmStr>("#t")),
        std::pair<uint32_t, std::shared_ptr<ScmObj> >(Defaults::boolean_false, nullptr),
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
        exit(1);
    }
}

void VM::apply_builtin(std::shared_ptr<ScmClosure> closure)
{
    if(!closure->built_in) {
        std::cout << "Called VM::apply_builtin on a non built in closure";
    }
    // All the built in functions are technically top level functions, so set the environment to top_level when executing them
    ENVT = top_level_env;
    
    BuiltInFunctions func = closure->func;
    if(func == BuiltInFunctions::addition) {


        // If let consumes the exact number of arguments it pushes on the stack
        // And only argument generation in let and a proc application causes the stack to grow,
        // This would mean that its guaranteed that the stack will be empty when a function is
        // called, So I THINK i could change this to consume any number of arguments
        is_stack_size(2, "+");

        auto a = STACK->top();
        STACK->pop();
        auto a_int = std::dynamic_pointer_cast<ScmInt>(a);
        if(a_int == nullptr) {
            std::cout << "Please provide a number to +" << std::endl;
            exit(1);
        }

        auto b = STACK->top();
        STACK->pop();
        auto b_int = std::dynamic_pointer_cast<ScmInt>(b);
        if(b_int == nullptr) {
            std::cout << "Please provide a number to +" << std::endl;
            exit(1);
        }

        auto ans = std::make_shared<ScmInt>(a_int->val + b_int->val);
        VALUE = ans;

    } else if(func == BuiltInFunctions::display) {

        is_stack_size(1, "display");
        auto obj = STACK->top();
        STACK->pop();
        if(obj == nullptr) {
            std::cout << "#f";
        } else {
            obj->print();
        }
        std::cout << std::endl;

    } else if(func == BuiltInFunctions::car) {
        
        is_stack_size(1, "car");
        auto obj = STACK->top();
        STACK->pop();
        auto fin = std::dynamic_pointer_cast<ScmPair>(obj);
        if(fin == nullptr) {
            std::cout << "not a pair, can't take car of it" << std::endl;
            exit(1);
        }
        VALUE = fin->car;

    } else if(func == BuiltInFunctions::cdr) {

        is_stack_size(1, "car");
        auto obj = STACK->top();
        STACK->pop();
        auto fin = std::dynamic_pointer_cast<ScmPair>(obj);
        if(fin == nullptr) {
            std::cout << "not a pair, can't take cdr of it" << std::endl;
            exit(1);
        }
        VALUE = fin->cdr;
        
    } else if(func == BuiltInFunctions::subtraction) {
        
        is_stack_size(2, "-");

        auto a = STACK->top();
        STACK->pop();
        auto a_int = std::dynamic_pointer_cast<ScmInt>(a);
        if(a_int == nullptr) {
            std::cout << "Please provide a number to -" << std::endl;
            exit(1);
        }

        auto b = STACK->top();
        STACK->pop();
        auto b_int = std::dynamic_pointer_cast<ScmInt>(b);
        if(b_int == nullptr) {
            std::cout << "Please provide a number to -" << std::endl;
            exit(1);
        }

        auto ans = std::make_shared<ScmInt>(a_int->val - b_int->val);
        VALUE = ans;

    } else if(func == BuiltInFunctions::division) {
        
        is_stack_size(2, "/");

        auto a = STACK->top();
        STACK->pop();
        auto a_int = std::dynamic_pointer_cast<ScmInt>(a);
        if(a_int == nullptr) {
            std::cout << "Please provide a number to /" << std::endl;
            exit(1);
        }

        auto b = STACK->top();
        STACK->pop();
        auto b_int = std::dynamic_pointer_cast<ScmInt>(b);
        if(b_int == nullptr) {
            std::cout << "Please provide a number to /" << std::endl;
            exit(1);
        }

        auto ans = std::make_shared<ScmInt>(a_int->val / b_int->val);
        VALUE = ans;

    } else if(func == BuiltInFunctions::multiplication) {
        
        is_stack_size(2, "*");

        auto a = STACK->top();
        STACK->pop();
        auto a_int = std::dynamic_pointer_cast<ScmInt>(a);
        if(a_int == nullptr) {
            std::cout << "Please provide a number to /" << std::endl;
            exit(1);
        }

        auto b = STACK->top();
        STACK->pop();
        auto b_int = std::dynamic_pointer_cast<ScmInt>(b);
        if(b_int == nullptr) {
            std::cout << "Please provide a number to *" << std::endl;
            exit(1);
        }

        auto ans = std::make_shared<ScmInt>(a_int->val * b_int->val);
        VALUE = ans;

    } else if(func == BuiltInFunctions::cons) {
        is_stack_size(2, "cons");
        auto a = STACK->top();
        STACK->pop();
        auto b = STACK->top();
        STACK->pop();
        VALUE = std::make_shared<ScmPair>(a, b);
    } else if(func == BuiltInFunctions::is_number) {
        is_stack_size(1, "number?");
        auto a = STACK->top();
        STACK->pop();
        auto a_int = std::dynamic_pointer_cast<ScmInt>(a);
        if(a_int == nullptr) {
            VALUE = constants[Defaults::boolean_false];
        } else {
            VALUE = constants[Defaults::boolean_true];
        }
    } else if(func == BuiltInFunctions::is_string) {
        is_stack_size(1, "string?");
        auto a = STACK->top();
        STACK->pop();
        auto a_str = std::dynamic_pointer_cast<ScmStr>(a);
        if(a_str == nullptr) {
            VALUE = constants[Defaults::boolean_false];
        } else {
            VALUE = constants[Defaults::boolean_true];
        }
    } else if(func == BuiltInFunctions::is_pair) {
        is_stack_size(1, "pair?");
        auto a = STACK->top();
        STACK->pop();
        auto a_pair = std::dynamic_pointer_cast<ScmPair>(a);
        if(a_pair == nullptr) {
            VALUE = constants[Defaults::boolean_false];
        } else {
            VALUE = constants[Defaults::boolean_true];
        }
    } else if(func == BuiltInFunctions::is_symbol) {
        is_stack_size(1, "symbol?");
        auto a = STACK->top();
        STACK->pop();
        auto a_sym = std::dynamic_pointer_cast<ScmSym>(a);
        if(a_sym == nullptr) {
            VALUE = constants[Defaults::boolean_false];
        } else {
            VALUE = constants[Defaults::boolean_true];
        }
    } else if(func == BuiltInFunctions::num_equal) {
        is_stack_size(2, "=");

        auto a = STACK->top();
        STACK->pop();
        auto a_int = std::dynamic_pointer_cast<ScmInt>(a);
        if(a_int == nullptr) {
            std::cout << "Please provide a number to =" << std::endl;
            exit(1);
        }

        auto b = STACK->top();
        STACK->pop();
        auto b_int = std::dynamic_pointer_cast<ScmInt>(b);
        if(b_int == nullptr) {
            std::cout << "Please provide a number to =" << std::endl;
            exit(1);
        }

        if(a_int->val == b_int->val) {
            VALUE = constants[Defaults::boolean_true];
        } else {
            VALUE = constants[Defaults::boolean_false];
        }
        
    } else if(func == BuiltInFunctions::eq) {
        is_stack_size(2, "eq?");
        auto a = STACK->top();
        STACK->pop();
        auto b = STACK->top();
        STACK->pop();
        
        if(a == b) {
            VALUE = constants[Defaults::boolean_true];
        } else {
            VALUE = constants[Defaults::boolean_false];
        }

        auto a_int = std::dynamic_pointer_cast<ScmInt>(a);
        if(a_int != nullptr) {
            auto b_int = std::dynamic_pointer_cast<ScmInt>(b);
            if(b_int != nullptr) {
                if(b_int->val == a_int->val) {
                    VALUE = constants[Defaults::boolean_true];
                }
            }
        }

        auto a_sym = std::dynamic_pointer_cast<ScmSym>(a);
        if(a_sym != nullptr) {
            auto b_sym = std::dynamic_pointer_cast<ScmSym>(b);
            if(b_sym != nullptr) {
                if(b_sym->val == a_sym->val) {
                    VALUE = constants[Defaults::boolean_true];
                }
            }
        }
    } else {
        std::cout << "Unrecognised function " << (int)func << std::endl;
    }
    pop_continuation();
}

void VM::fetch_execute(void)
{
    uint8_t code;
    read_byte(&code);
    check_file();
    while(code != OppCodes::ext) {
        if(code == OppCodes::opp_null) {
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
            }
            if(closure->built_in) {
                apply_builtin(closure);
            } else {
                ENVT = closure->closure_env;
                // !! This is a converstion from unsigned int to int, which might be lossy !!
                file.seekg(closure->porc_address);
                check_file();
            }
            // Need to read in the next instruction to process
            read_byte(&code);
            check_file();
            continue;
        } else if (code == OppCodes::ret) {
            pop_continuation();
        } else if (code == OppCodes::save_continuation) {
            uint32_t resume_address;
            read_4_bytes(&resume_address);
            auto new_cont = std::make_shared<ScmCont>(resume_address, ENVT, STACK, CONT);
            CONT = new_cont;
        } else if (code == OppCodes::if_false_branch) {
            uint32_t branch_address;
            read_4_bytes(&branch_address);
            if(VALUE == nullptr) {
                file.seekg(branch_address);
                check_file();
            }
        } else if (code == OppCodes::if_true_branch) {
            uint32_t branch_address;
            read_4_bytes(&branch_address);
            if(VALUE != nullptr) {
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
            auto val = lookup_var(var);
            if(val == nullptr) {
                std::cout << "Unable to set " << var << " could not find value" << std::endl;
                exit(1);
            }
            val = VALUE;
        } else if (code == OppCodes::define) {
            std::string var = read_string();
            auto val = top_level_env->map->find(var);
            if(val != top_level_env->map->end()) {
                std::cout << "Unable to define " << var << " , value already exists";
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
        } else {
            std::cout << "Unknown instruction " << (int) code << " At position " << std::hex << (int)(file.tellg()) << std::endl;
            exit(1);
        }
        read_byte(&code);
    }
    std::cout << "Program exit" << std::endl;
    
}

int main(int argc, char** argv)
{
    if(argc < 2) {
        std::cout << "Usage: vm <compiled_file_name>" << std::endl;
        return -1;
    }
    std::ifstream file(argv[1], std::ios::binary);
    if(!file) {
        std::cout << "Error opening file\n";
        return 1;
    }
    VM virtual_machine = VM(file);
    virtual_machine.run();
}