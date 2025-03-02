#include "vm.h"

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
        std::string o;
        if(obj == nullptr) {
            o = "#f";
            std::cout << o;
        } else {
            o = obj->to_str();
            std::cout << o;
        }
        cur_out = o;
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
        
        if(STACK->size() == 1) {
            auto a = STACK->top();
            STACK->pop();
            auto a_int = std::dynamic_pointer_cast<ScmInt>(a);
            if(a_int == nullptr) {
                std::cout << "Please provide a number to -" << std::endl;
                exit(1);
            } else {
                VALUE = std::make_shared<ScmInt>(-(a_int->val));
            }
        } else {
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
        }
        

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
    } else if(func == BuiltInFunctions::num_greater){
        is_stack_size(2, ">");

        auto a = STACK->top();
        STACK->pop();
        auto a_int = std::dynamic_pointer_cast<ScmInt>(a);
        if(a_int == nullptr) {
            std::cout << "Please provide a number to >" << std::endl;
            exit(1);
        }

        auto b = STACK->top();
        STACK->pop();
        auto b_int = std::dynamic_pointer_cast<ScmInt>(b);
        if(b_int == nullptr) {
            std::cout << "Please provide a number to >" << std::endl;
            exit(1);
        }

        if(a_int->val > b_int->val) {
            VALUE = constants[Defaults::boolean_true];
        } else {
            VALUE = constants[Defaults::boolean_false];
        }

    } else if(func == BuiltInFunctions::num_greater_equal){
        is_stack_size(2, ">=");

        auto a = STACK->top();
        STACK->pop();
        auto a_int = std::dynamic_pointer_cast<ScmInt>(a);
        if(a_int == nullptr) {
            std::cout << "Please provide a number to >=" << std::endl;
            exit(1);
        }

        auto b = STACK->top();
        STACK->pop();
        auto b_int = std::dynamic_pointer_cast<ScmInt>(b);
        if(b_int == nullptr) {
            std::cout << "Please provide a number to >=" << std::endl;
            exit(1);
        }

        if(a_int->val >= b_int->val) {
            VALUE = constants[Defaults::boolean_true];
        } else {
            VALUE = constants[Defaults::boolean_false];
        }

    } else if(func == BuiltInFunctions::num_less){

        is_stack_size(2, "<");

        auto a = STACK->top();
        STACK->pop();
        auto a_int = std::dynamic_pointer_cast<ScmInt>(a);
        if(a_int == nullptr) {
            std::cout << "Please provide a number to <" << std::endl;
            exit(1);
        }

        auto b = STACK->top();
        STACK->pop();
        auto b_int = std::dynamic_pointer_cast<ScmInt>(b);
        if(b_int == nullptr) {
            std::cout << "Please provide a number to <" << std::endl;
            exit(1);
        }

        if(a_int->val < b_int->val) {
            VALUE = constants[Defaults::boolean_true];
        } else {
            VALUE = constants[Defaults::boolean_false];
        }
    } else if(func == BuiltInFunctions::num_less_equal){
        is_stack_size(2, "<=");

        auto a = STACK->top();
        STACK->pop();
        auto a_int = std::dynamic_pointer_cast<ScmInt>(a);
        if(a_int == nullptr) {
            std::cout << "Please provide a number to <=" << std::endl;
            exit(1);
        }

        auto b = STACK->top();
        STACK->pop();
        auto b_int = std::dynamic_pointer_cast<ScmInt>(b);
        if(b_int == nullptr) {
            std::cout << "Please provide a number to <=" << std::endl;
            exit(1);
        }

        if(a_int->val <= b_int->val) {
            VALUE = constants[Defaults::boolean_true];
        } else {
            VALUE = constants[Defaults::boolean_false];
        }

    } else {
        std::cout << "Unrecognised function " << (int)func << std::endl;
    }
    pop_continuation();
}