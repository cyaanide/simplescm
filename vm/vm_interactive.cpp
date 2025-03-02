#include "vm.h"
#include <iterator>

ftxui::Element VM::draw_value_register()
{
    if(VALUE != nullptr) {
        return ftxui::text("VALUE: " + VALUE->to_str());
    } else {
        return ftxui::text("VALUE:" );
    }
}

void VM::clear_out(void)
{
    cur_out.clear();
}

ftxui::Element VM::draw_current_out(void)
{
    return ftxui::text(cur_out);
}

bool VM::print_instruction(std::string& out)
{
    uint8_t code;
    read_byte(&code);
    if(code == OppCodes::ext) {
        out = "ext";
        return false;
    } else if(code == OppCodes::opp_null) {
        // Nothing to do
        out = "null_opp";
    } else if (code == OppCodes::lookup) {
        auto var = read_string();
        check_file();
        out =  "lookup " + var;
    } else if (code == OppCodes::load_const) {
        uint32_t uid;
        read_4_bytes(&uid);
        check_file();
        out = (std::string("load_const ") + std::string("<") + std::to_string(uid) + std::string(">"));
    } else if (code == OppCodes::bind) {
        std::string temp = "bind ";
        uint8_t no_vars;
        read_byte(&no_vars);
        check_file();
        temp += std::to_string(no_vars);
        temp += " ";
        for(auto i = 0; i < no_vars; i++) {
            auto var_str = read_string();
            check_file();
            temp += var_str + " ";
        }
        out = temp;
    } else if (code == OppCodes::apply) {
        out =  "apply";
    } else if (code == OppCodes::ret) {
        out = "ret";
    } else if (code == OppCodes::save_continuation) {
        uint32_t resume_address;
        read_4_bytes(&resume_address);
        // out = "save_cont " + std::to_string(resume_address);
        std::stringstream stream;
        stream << "0x"  << std::hex << std::uppercase << resume_address;
        out = (std::string("save_cont ") + stream.str());
    } else if (code == OppCodes::if_false_branch) {
        uint32_t branch_address;
        read_4_bytes(&branch_address);
        std::stringstream stream;
        stream << "0x"  << std::hex << std::uppercase << branch_address;
        out = "if_false_branch " + stream.str();
    } else if (code == OppCodes::if_true_branch) {
        uint32_t branch_address;
        read_4_bytes(&branch_address);
        std::stringstream stream;
        stream << "0x" << std::hex << std::uppercase << branch_address;
        out = "if_true_branch " + stream.str();
    } else if (code == OppCodes::branch) {
        uint32_t branch_address;
        read_4_bytes(&branch_address);
        std::stringstream stream;
        stream << "0x" << std::hex << std::uppercase << branch_address;
        out = "branch " + stream.str();
    } else if (code == OppCodes::push) {
        out = "push";
    } else if (code == OppCodes::make_closure) {
        uint32_t branch_address;
        read_4_bytes(&branch_address);
        std::stringstream stream;
        stream << "0x" << std::hex << std::uppercase << branch_address;
        out = "make_closure " + stream.str();
    } else if (code == OppCodes::set) {
        std::string var = read_string();
        out = "set " + var;
    } else if (code == OppCodes::define) {
        std::string var = read_string();
        out = "define " + var;
    } else if (code == OppCodes::label) {
        out = "label";
    } else if (code == OppCodes::proc_end) {
        out = "proc_end";
        return false;
    } else if (code == OppCodes::data_start || code == OppCodes::data_end || code == OppCodes::const_data) {
        out = "!!data_instruction!!";
        return false;
    } else if(code == OppCodes::unbind) {
        out = "unbind";
    } else {
        std::cout << "Unknown instruction " << (int) code << " At position " << std::hex << (int)(file.tellg()) << std::endl;
        out = "!!unknown!!";
        return false;
    }
    return true;
}

ftxui::Element VM::draw_stack()
{
    auto restore = std::make_shared<scm_stack>();
    ftxui::Elements r;
    r.push_back(ftxui::filler());
    while(!STACK->empty())
    {
        r.push_back(ftxui::separatorLight() | ftxui::dim);
        r.push_back(ftxui::text(STACK->top()->to_str()) | ftxui::center);
        restore->push(STACK->top());
        STACK->pop();
    }
    while(!restore->empty())
    {
        STACK->push(restore->top());
        restore->pop();
    }
    return ftxui::vbox(r);
}

ftxui::Element VM::draw_environment(void)
{
    auto is_built_in = [](const std::pair<std::string, std::shared_ptr<ScmObj> >& p) {
        auto c = std::dynamic_pointer_cast<ScmClosure>(p.second);
        if(c) {
            return c->built_in;
        }
        return false;
    };
    ftxui::Elements vars;
    ftxui::Elements values;
    for(const auto& i: *(ENVT->map)) {
        if(!is_built_in(i)) {
            vars.push_back(ftxui::text(i.first));
            values.push_back(ftxui::text(i.second->to_str()));
            values.push_back(ftxui::separatorLight() | ftxui::dim);
            vars.push_back(ftxui::separatorLight() | ftxui::dim);
        }
    }
    return ftxui::hbox({ftxui::vbox(vars) | ftxui::flex,
                        ftxui::vbox(values)}) | ftxui::flex;
}

ftxui::Element VM::draw_prev_environment(void)
{
    auto is_built_in = [](const std::pair<std::string, std::shared_ptr<ScmObj> >& p) {
        auto c = std::dynamic_pointer_cast<ScmClosure>(p.second);
        if(c) {
            return c->built_in;
        }
        return false;
    };
    auto prev_env = ENVT;
    if(ENVT->prev) {
        prev_env = ENVT->prev;
    } else {
        return ftxui::hbox();
    }
    ftxui::Elements vars;
    ftxui::Elements values;
    for(const auto& i: *(prev_env->map)) {
        if(!is_built_in(i)) {
            vars.push_back(ftxui::text(i.first));
            values.push_back(ftxui::text(i.second->to_str()));
            values.push_back(ftxui::separatorLight() | ftxui::dim);
            vars.push_back(ftxui::separatorLight() | ftxui::dim);
        }
    }
    return ftxui::hbox({ftxui::vbox(vars) | ftxui::flex,
                        ftxui::vbox(values)}) | ftxui::flex;
}

ftxui::Element VM::draw_instructions()
{
    auto backup = file.tellg();
    ftxui::Elements o;
    if(backup >= file_size) {
        return ftxui::vbox(o);

    }
    std::streampos cur_pos;
    for(int i = 0; i < 15; i++) {
        std::string a;
        bool done = false;
        cur_pos = file.tellg();
        check_file();
        if(!print_instruction(a)) {
            done = true;
        }
        std::stringstream in_hex;
        in_hex << "0x" << std::hex << std::uppercase << (int) cur_pos;
        auto t = ftxui::hbox({ftxui::text(in_hex.str()) | ftxui::flex , ftxui::text(a)});
        if(i != 0) {
            t |= ftxui::dim;
        }
        o.push_back(t);
        o.push_back(ftxui::separatorLight() | ftxui::dim);
        if(done) {
            break;
        }
    }
    file.seekg(backup);
    return ftxui::vbox(o);
}
