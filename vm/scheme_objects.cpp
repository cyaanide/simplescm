#include "scheme_objects.h"

ScmClosure::ScmClosure(bool built_in, BuiltInFunctions func, uint32_t address, std::shared_ptr<ScmEnv> envt)
    : built_in(built_in), func(func), porc_address(address), closure_env(envt)
{
}

ScmEnv::ScmEnv(std::shared_ptr<ScmEnv> prev_initial): prev(prev_initial)
{
    map = std::make_shared<env_map>();
}

void ScmInt::print(void)
{
    std::cout << " " << val << " ";
    return;
}

void ScmSym::print(void)
{
    std::cout << " '" << val << " ";
}

void ScmStr::print(void)
{
    std::cout << " " << val << " ";
}

void ScmClosure::print(void)
{
    if(built_in) {
        std::cout << "Built_in_procedure " << func << " ";
    } else {
        std::cout << "user_defined_procedure " << std::hex << porc_address << " ";
    }
}

void ScmPair::print(void)
{
    if(car == nullptr) {
        std::cout << " () ";
        return;
    } 
    
    std::cout << " (";
    car->print();
    std::cout << ".";
    cdr->print();
    std::cout << " )";
}