#include "compiler_enums.h"
#include <unordered_map>
#include <stack>
#include <string>
#include <iostream>

// typedef std::unordered_map<std::string, std::shared_ptr<ScmObj>> environment;

class ScmObj
{
    public:
    virtual void print(void) = 0;
};

using env_map = std::unordered_map<std::string, std::shared_ptr<ScmObj>>;

class ScmEnv {

    public:
    std::shared_ptr<ScmEnv> prev;
    std::shared_ptr<env_map> map;
    ScmEnv(std::shared_ptr<ScmEnv> prev_initial);
    
};

class ScmInt : public ScmObj
{
    public:
    double val;
    void print(void) override;
    ScmInt(double initial) : val(initial) {}
};

class ScmStr : public ScmObj
{
    public:
    std::string val;
    void print(void) override;
    ScmStr(std::string initial): val(initial) {}

};

class ScmSym : public ScmObj
{
    public:
    std::string val;
    void print(void) override;
    ScmSym(std::string initial): val(initial) {}

};

class ScmPair : public ScmObj
{
    public:
    std::shared_ptr<ScmObj> car;
    std::shared_ptr<ScmObj> cdr;
    void print(void) override;
    ScmPair(std::shared_ptr<ScmObj> initial_car, std::shared_ptr<ScmObj> initial_cdr) : car(initial_car), cdr(initial_cdr) {}
};

// class ScmBool : public ScmObj
// {
//     public:
//     bool val;
//     void print(void) override;
//     ScmBool(bool initial): val(initial) {}
    
// };

class ScmClosure : public ScmObj
{
    public:
    bool built_in;
    BuiltInFunctions func;
    u_int32_t porc_address;
    std::shared_ptr<ScmEnv> closure_env;

    void print(void) override;
    ScmClosure(bool built_in, BuiltInFunctions func, uint32_t address, std::shared_ptr<ScmEnv> envt);

};

using scm_stack = std::stack<std::shared_ptr<ScmObj> >;

class ScmCont {
    public:
    uint32_t resume_loc;
    std::shared_ptr<ScmEnv> env;
    std::shared_ptr<scm_stack> saved_stack;
    std::shared_ptr<ScmCont> prev;
    ScmCont(uint32_t resume_loc_initial, std::shared_ptr<ScmEnv> env_initial, std::shared_ptr<scm_stack> saved_stack_initial, std::shared_ptr<ScmCont> prev_initial):
        resume_loc(resume_loc_initial), env(env_initial), saved_stack(saved_stack_initial), prev(prev_initial) {}
};
