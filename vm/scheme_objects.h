#include "compiler_enums.h"
#include <cstdint>

// typedef std::unordered_map<std::string, std::shared_ptr<ScmObj>> environment;

class ScmObj
{
    public:
    virtual void print(void) = 0;
};

using environment = std::unordered_map<std::string, std::shared_ptr<ScmObj>>;

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
    void print(void) override;
    ScmClosure(bool built_in, BuiltInFunctions func, uint32_t address, std::shared_ptr<environment> envt);

    // A pointer to the environment
    u_int32_t porc_address;
};
