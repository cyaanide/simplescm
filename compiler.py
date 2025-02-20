import sys
from expressions import *
from compilerenums import *
from assembler import *
from astgenerator import *




class Compiler():
    def __init__(self, ast):
        self.ast = ast
        # A list of tuples (uid, (Type, [vals,]))
        self.constants = []
        # A list of tuples (Opp, Input)
        self.instructions = []
        # A list of tuple of (procedure_id, instructions)
        self.procedures = []
        # Reserve some initial cuid's, this way I can directly use them 
        self.cur_uid = len(Defaults)
    
    def generate_uid(self):
        self.cur_uid += 1
        return self.cur_uid
        
    def is_type_default(self, exp):
        return isinstance(exp, Defaults)

    # just return the list of pre_requisite labels
    def compile_list_constant(self, expression):
        if(not isinstance(expression, SConstList)):
            raise SynError(str(expression) + "is not a SConstList")
        consts = expression.consts
        consts_uids = []
        for exp in consts:
                (exp_uid, exp_data, _) = self.generate_data_instruction_for_constant(exp)
                consts_uids.append(exp_uid)
                if(not self.is_type_default(exp_data[0])):
                    self.constants.append((exp_uid, exp_data))
                    
        return consts_uids

    def is_default_label(self, label):
        if(label.startswith("bool") or label.startswith("empty_list")):
            return True
        return False
            
    # Return (uid, data, instruction)
    def generate_data_instruction_for_constant(self, expression):
        if(not isinstance(expression, SConstant)):
            raise SynError(str(expression) + "is not a SConstant")
        uid = None
        data = None
        instruction = None
        if(isinstance(expression, SNumber)):
            # label = self.generate_label("num")
            uid = self.generate_uid()
            # data = "number " + str(expression.value)
            data = (Types.number, [expression.value,])
            # instruction = ("load_const " + label)
            instruction = (OppCodes.load_const, uid)
        elif(isinstance(expression, SString)):
            # label = self.generate_label("str")
            uid = self.generate_uid()
            # data = "string " + expression.value
            data = (Types.string, [expression.value,])
            # instruction = "load_const " + label
            instruction = (OppCodes.load_const, uid)
        elif(isinstance(expression, SBool)):
            # data = "boolean " + str(expression.value)
            # data = (OppCodes.boolean, 1, expression.value)
            # instruction = "load_const " + label
            val = Defaults.boolean_true if expression.value else Defaults.boolean_false
            uid = val.value
            data = (val, [uid,])
            instruction = (OppCodes.load_const, uid)
        elif(isinstance(expression, SSymbol)):
            # label = self.generate_label("symbol")
            uid = self.generate_uid()
            # data = "symbol " + expression.value
            data = (Types.symbol, [expression.value,])
            # instruction = "load_const " + label
            instruction = (OppCodes.load_const, uid)
        elif(isinstance(expression, SEmptyList)):
            val = Defaults.empty_list
            uid = val.value
            data = (val, [uid,])
            instruction = (OppCodes.load_const, uid)
        elif(isinstance(expression, SConstList)):
            uids = self.compile_list_constant(expression)
            # label = self.generate_label("list")
            uid = self.generate_uid()
            # data = "list " + str(len(pre_req_const_labels)) + " " +  " ".join(pre_req_const_labels)
            data = (Types.list, uids)
            instruction = (OppCodes.load_const, uid)
            # instruction = "load_const " + label
        else:
            raise SynError("Exhausted all possibilites of SConstant, instead is of type " + str(type(expression)))

        if(uid and data and instruction):
            return (uid, data, instruction)

    def compile_constant(self, list_to_add_to,  expression, tail):
        (uid, data, instruction) = self.generate_data_instruction_for_constant(expression)
        list_to_add_to.append(instruction)
        if(not self.is_type_default(data[0])):
            self.constants.append((uid, data))
        if(tail):
            list_to_add_to.append((OppCodes.ret, None))
        
    def compile_if(self, list_to_add_to, expression, tail):
        if(not isinstance(expression, SIf)):
            raise SynError("Not an SIf expression, instead of type: " + str(type(expression)))
        # Compile the test
        self.compile_expression(list_to_add_to, expression.test, False)
        false_branch_uid = self.generate_uid()
        if_end_branch_uid = self.generate_uid()

        list_to_add_to.append((OppCodes.if_false_branch, false_branch_uid))
        self.compile_expression(list_to_add_to, expression.consequent, tail)
        list_to_add_to.append((OppCodes.branch, if_end_branch_uid))
        list_to_add_to.append((OppCodes.label, false_branch_uid))
        self.compile_expression(list_to_add_to, expression.alternative, tail)
        list_to_add_to.append((OppCodes.label, if_end_branch_uid))
        
    def compile_lambda(self, list_to_add_to, expression, tail):
        ins = []
        if(not isinstance(expression, SLambda)):
            raise SynError("Not an SLambda expression, instead of type: " + str(type(expression)))
        uid = self.generate_uid()
        var_bound_list_str = list(map(str, expression.bound_var_list))
        ins.append((OppCodes.bind, var_bound_list_str))
        self.compile_sequence(ins, expression.body, True)
        ins.append((OppCodes.proc_end, None))
        list_to_add_to.append((OppCodes.make_closure, uid))
        if(tail):
            list_to_add_to.append((OppCodes.ret, None))
        self.procedures.append((uid, ins))
       
    def compile_sequence(self, list_to_add_to, sequence, tail):
        len_sequence = len(sequence)
        for i in range(len_sequence - 1):
            self.compile_expression(list_to_add_to, sequence[i], False)
        if(len_sequence != 0):
            self.compile_expression(list_to_add_to, sequence[len_sequence - 1], tail)
    
    def compile_variable(self, list_to_add_to, expression, tail):
        if(not isinstance(expression, SVariable)):
            raise SynError("Not an SVariable expression, instead of type: " + str(type(expression)))
        list_to_add_to.append((OppCodes.lookup, expression.value))
        if(tail):
            list_to_add_to.append((OppCodes.ret, None))
    
    def compile_arguments(self, list_to_add_to, arguments, tail=False):
        if(tail):
            raise SynError("Tail should always be false when compiling arguments")
        for arg in arguments[::-1]:
            self.compile_expression(list_to_add_to, arg, False)
            list_to_add_to.append((OppCodes.push, None))
        
    def compile_proc_application(self, list_to_add_to, expression, tail):
        if(not isinstance(expression, SProcApplication)):
            raise SynError("Not an SProcApplication expression, instead of type: " + str(type(expression)))
        uid = None
        if(not tail):
            uid = self.generate_uid()
            list_to_add_to.append((OppCodes.save_continuation, uid))
            
        # Evaluate the arguments
        self.compile_arguments(list_to_add_to, expression.operands, False)
        self.compile_expression(list_to_add_to, expression.operator, False)
        list_to_add_to.append((OppCodes.apply, None))

        if(not tail):
            list_to_add_to.append((OppCodes.label, uid))
            
    # Defines are only allowed to be top level
    def compile_define(self, list_to_add_to, expression, tail):
        # Define should always be a top level expression
        if(tail):
            raise SynError("Define in tail posisiton, not allowed")
        if(not isinstance(expression, SDefine)):
            raise SynError("Expression is not of type SDefine, instead is of type " + str(type(expression)))
        self.compile_expression(list_to_add_to, expression.expression, False)
        list_to_add_to.append((OppCodes.define, expression.var))

    # Set is allowed to be anywhere it wants to be, the result of the set expression will be the new value of the computed argument
    def compile_set(self, list_to_add_to, expression, tail):
        if(not isinstance(expression, SSet)):
            raise SynError("Expression is not of type SSet, instead is of type " + str(type(expression)))
        # Compute the argument to set in non tail position
        self.compile_expression(list_to_add_to, expression.expression, False)
        list_to_add_to.append((OppCodes.set, expression.variable))
        if(tail):
            list_to_add_to.append("return")
    
    def compile_and(self, list_to_add_to, expression, tail):
        if(not isinstance(expression, SAnd)):
            raise SynError("Expression is not of type SAnd, instead is of type " + str(type(expression)))
        and_false_uid = self.generate_uid()
        and_end_uid = self.generate_uid()
        for exp in expression.expressions:
            self.compile_expression(list_to_add_to, exp, False)
            list_to_add_to.append((OppCodes.if_false_branch, and_false_uid))
        list_to_add_to.append((OppCodes.load_const, Defaults.boolean_true.value))
        if(tail):
            list_to_add_to.append((OppCodes.ret, None))
        list_to_add_to.append((OppCodes.branch, and_end_uid))
        list_to_add_to.append((OppCodes.label, and_false_uid))
        list_to_add_to.append((OppCodes.load_const, Defaults.boolean_false.value))

        if(tail):
            list_to_add_to.append((OppCodes.ret, None))
        list_to_add_to.append((OppCodes.label, and_end_uid))
            
    def compile_or(self, list_to_add_to, expression, tail):
        if(not isinstance(expression, SOr)):
            raise SynError("Expression is not of type SOr, instead is of type " + str(type(expression)))
        or_true_uid = self.generate_uid()
        or_end_uid = self.generate_uid()

        for exp in expression.expressions:
            self.compile_expression(list_to_add_to, exp, False)
            list_to_add_to.append((OppCodes.if_true_branch, or_true_uid))
        list_to_add_to.append((OppCodes.load_const, Defaults.boolean_false.value))
        if(tail):
            list_to_add_to.append((OppCodes.ret, None))
        list_to_add_to.append((OppCodes.branch, or_end_uid))
        list_to_add_to.append((OppCodes.label, or_true_uid))
        list_to_add_to.append((OppCodes.load_const, Defaults.boolean_true.value))
        if(tail):
            list_to_add_to.append((OppCodes.ret, None))
        list_to_add_to.append((OppCodes.label, or_end_uid))
        
    def compile_let(self, list_to_add_to, expression, tail):
        if(not isinstance(expression, SLet)):
            raise SynError("Expression is not of type SLet, instead is of type " + str(type(expression)))
        bindings = [x[1] for x in expression.var_bindings]
        vars = [x[0] for x in expression.var_bindings]
        vars = list(map(str, vars))
        self.compile_arguments(list_to_add_to, bindings, False)
        list_to_add_to.append((OppCodes.bind, vars))
        self.compile_sequence(list_to_add_to, expression.body, tail)
        
    def compile_expression(self, list_to_add_to,  expression, tail):
        if(isinstance(expression, SConstant)):
            self.compile_constant(list_to_add_to, expression, tail)
        elif(isinstance(expression, SVariable)):
            self.compile_variable(list_to_add_to, expression, tail)
        elif(isinstance(expression, SIf)):
            self.compile_if(list_to_add_to, expression, tail)
        elif(isinstance(expression, SLambda)):
            self.compile_lambda(list_to_add_to, expression, tail)
        elif(isinstance(expression, SProcApplication)):
            self.compile_proc_application(list_to_add_to, expression, tail)
        elif(isinstance(expression, SDefine)):
            self.compile_define(list_to_add_to, expression, tail)
        elif(isinstance(expression, SSet)):
            self.compile_set(list_to_add_to, expression, tail)
        elif(isinstance(expression, SAnd)):
            self.compile_and(list_to_add_to, expression, tail)
        elif(isinstance(expression, SOr)):
            self.compile_or(list_to_add_to, expression, tail)
        elif(isinstance(expression, SBegin)):
            self.compile_sequence(list_to_add_to, expression.expressions, tail)
        elif(isinstance(expression, SLet)):
            self.compile_let(list_to_add_to, expression, tail)
        else:
            raise SynError("Reached the end of expression case switch, unknown expression of type " + str(type(expression)))
        
    def compile(self):
        for exp in self.ast:
            # All top level expressions are always in non tail position
            self.compile_expression(self.instructions, exp, False)
        self.instructions.append((OppCodes.ext, None))
        return(self.constants, self.instructions, self.procedures)
    
    def generate_human_readable(self):
        def print_ins(instructions):
            output = ""
            for ins in instructions:
                output += (ins[0]).name + " " + (str(ins[1]) if ins[1] != None else "") + "\n"
            return output
            
        output = ""
        output += ".defaults_start\n"
        for default in Defaults:
            output += "uid: " + str(default.value) + " name: " + default.name + "\n"
        output+=  ".defaults_end\n\n"
        
        output += ".data_start\n"
        for dat in self.constants:
            output += "uid: " + str(dat[0]) + " type: " + dat[1][0].name
            output += " val(s): " + str(dat[1][1])
            output += "\n"
        output += ".data_end\n\n"

        output += print_ins(self.instructions)
        
        output += "\n"
        for proc in self.procedures:
            output += "lambda " + str(proc[0]) + "\n"
            output += print_ins(proc[1])
            output += "\n"
        output += "\n"

        return output
                                                                                                                

if __name__ == "__main__":
    def pretty_print_hex(body):
        for ins in body:
            print(", ".join(hex(b) for b in ins))

    filename = sys.argv[1]
    with open(filename) as file_name:
        code = file_name.read()
    ast_generator = ASTGenerator(code)
    tokens = ast_generator.produce_tokens()
    compiler = Compiler(tokens)
    (data, instructions, procedure) = compiler.compile()
    output = compiler.generate_human_readable()
    print(output, end='')
    assembler = Assembler(data, instructions, procedure)
    assembler.assemble_constants()
    (body, to_replace, label_loc, proc_locs) = assembler.assemble_body(instructions)
    pretty_print_hex(body=body)
    print(to_replace)
    print(label_loc)
    print(proc_locs)
    (body, to_replace, label_loc, proc_locs) = assembler.assemble_body(procedure[0][1])
    pretty_print_hex(body=body)
    print(to_replace)
    print(label_loc)
    print(proc_locs)


    


