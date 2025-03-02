#include "scheme_objects.h"
#include <sstream>

ScmClosure::ScmClosure(bool built_in, BuiltInFunctions func, uint32_t address, std::shared_ptr<ScmEnv> envt)
    : built_in(built_in), func(func), porc_address(address), closure_env(envt)
{
}

ScmEnv::ScmEnv(std::shared_ptr<ScmEnv> prev_initial): prev(prev_initial)
{
    map = std::make_shared<env_map>();
}

std::string ScmInt::to_str(void)
{
    return std::to_string(val); 
}

void ScmInt::print(void)
{
    std::cout << to_str();
    return;
}

std::string ScmSym::to_str(void)
{
    return val;
}

void ScmSym::print(void)
{
    std::cout << to_str();
    return;
}

std::string ScmStr::to_str(void)
{
    return val;
}

void ScmStr::print(void)
{
    std::cout << to_str();
    return;
}

std::string ScmBool::to_str(void)
{
    std::string str;
    if(val) {
        str = "#t";
    } else {
        str = "#f";
    }
    return str;
}

void ScmBool::print(void)
{
    std::cout << to_str();
}

std::string ScmClosure::to_str(void)
{
    if(built_in) {
        std::stringstream stream;
        stream << "0x" << std::hex << std::uppercase << (int) func;
        return "<built_in_proc " + stream.str() + ">";
    } else {
        std::stringstream stream;
        stream << "0x" << std::hex << std::uppercase << (int) porc_address;
        return "<proc " + stream.str() + ">";
    }
}

void ScmClosure::print(void)
{
    std::cout << to_str();
}

std::string ScmPair::to_str(void)
{
    std::string ans;
    if(car == nullptr) {
        ans = "()";
        return ans;
    } 
    ans += "( ";
    ans += car->to_str();
    ans += " . ";
    ans += cdr->to_str();
    ans += " )";
    return ans;
}

void ScmPair::print(void)
{
    std::cout << to_str();
}