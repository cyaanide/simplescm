#include "vm.h"

#define READ_BYTES(var, bytes) file.read(reinterpret_cast<char*>(&var), bytes); check_file()

VM::VM(std::ifstream& source): file(source)
{
    file.seekg(0, std::ios::end);
    file_size = file.tellg();
    file.seekg(0, std::ios::beg);
    top_lvl_environment = std::make_shared<environment>();
}

void VM::read_byte(uint8_t* dest)
{
    file.read(reinterpret_cast<char*>(dest), 1);
    check_file();
}

void VM::read_4_bytes(uint32_t* dest)
{
    file.read(reinterpret_cast<char*>(dest), 4);
    check_file();
} 

void VM::read_double(double* dest)
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

void VM::check_file(void)
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
            auto list_uids = std::vector<uint32_t>();
            for(int i = 0; i < len_list; i++) {
                uint32_t uid;
                read_4_bytes(&uid);
                // std::cout << "list elem uid is " << uid << std::endl;
                list_uids.push_back(uid);
            }
            
            std::shared_ptr<ScmObj> cur = constants[Defaults::empty_list];
            for(int i = len_list - 1; i >= 0; i--) {
                cur = std::make_shared<ScmPair>(constants[list_uids[i]], cur);
            }

            constants[uid] = cur;
            // print_list(uid);
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
        auto closure = std::make_shared<ScmClosure>(true, static_cast<BuiltInFunctions>(i), 0, top_lvl_environment);
        top_lvl_environment->insert(std::pair<std::string, std::shared_ptr<ScmObj> >(proc_name, closure));
    }
    constants = {
        std::pair<uint32_t, std::shared_ptr<ScmObj> >(Defaults::boolean_true, std::make_shared<ScmInt>(1)),
        std::pair<uint32_t, std::shared_ptr<ScmObj> >(Defaults::boolean_false, nullptr),
        std::pair<uint32_t, std::shared_ptr<ScmObj> >(Defaults::empty_list, std::make_shared<ScmPair>(nullptr, nullptr)),
    };
}

int main(int argc, char** argv) {
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