from expressions import *
from compilerenums import *
from astgenerator import *
from assembler import *
import sys
import getopt


class Compiler():


    def __init__(self, ast):
        """Comiler constructor

        Args:
            ast (List<SExpression>): Abstract Syntax Tree to be compiled
        """
        self.ast = ast
        # A list of tuples (uid, (Type, [vals,]))
        self.constants = []
        # A list of tuples (Opp, Input)
        self.instructions = []
        # A list of tuple of (procedure_id, instructions)
        self.procedures = []
        # Reserve some uid's for the scheme defaults
        self.cur_uid = len(Defaults)


    def generate_uid(self):
        """Generate UID

        Returns:
            int: The next UID
        """
        self.cur_uid += 1
        return self.cur_uid


    def is_type_default(self, exp):
        """Is exp of instance Default

        Args:
            exp (Any):

        Returns:
            boolean: True if exp is of instance Defaults
        """
        return isinstance(exp, Defaults)
    

    def compile_list_constant(self, expression):
        """Compile SConstList, append the constants to self.constants and return the list of UIDs of the constants

        Args:
            expression (SConstList): The SConstList to compile

        Raises:
            SynError: raises error of expression is not of type SConstList

        Returns:
            List: UIDs of the constants present in the list
        """
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


    def generate_data_instruction_for_constant(self, expression):
        """Generate the uid, data to be written to the constants section and the instruction to load this constant

        Args:
            expression (SConstant): The constant to generate the output for

        Returns:
            (uid, data, instruction):
        """
        if(not isinstance(expression, SConstant)):
            raise SynError(str(expression) + "is not a SConstant")
        uid = None
        data = None
        instruction = None
        if(isinstance(expression, SNumber)):
            uid = self.generate_uid()
            data = (Types.number, [expression.value,])
            instruction = (OppCodes.load_const, uid)
        elif(isinstance(expression, SString)):
            uid = self.generate_uid()
            data = (Types.string, [expression.value,])
            instruction = (OppCodes.load_const, uid)
        elif(isinstance(expression, SBool)):
            val = Defaults.boolean_true if expression.value else Defaults.boolean_false
            uid = val.value
            data = (val, [uid,])
            instruction = (OppCodes.load_const, uid)
        elif(isinstance(expression, SSymbol)):
            uid = self.generate_uid()
            data = (Types.symbol, [expression.value,])
            instruction = (OppCodes.load_const, uid)
        elif(isinstance(expression, SEmptyList)):
            val = Defaults.empty_list
            uid = val.value
            data = (val, [uid,])
            instruction = (OppCodes.load_const, uid)
        elif(isinstance(expression, SConstList)):
            uids = self.compile_list_constant(expression)
            uid = self.generate_uid()
            data = (Types.list, uids)
            instruction = (OppCodes.load_const, uid)
        else:
            raise SynError("Exhausted all possibilites of SConstant, instead is of type " + str(type(expression)))

        if(uid and data and instruction):
            return (uid, data, instruction)
        else:
            raise SynError("Logic error when compiling constant")


    def compile_constant(self, list_to_add_to,  expression, tail):
        """Compile a constant

        Args:
            list_to_add_to (List): The list to add the load / return instruction to when compiling this constant
            expression (SConstant): The expression to compile
            tail (boolean): Is expression in tail position
        """
        (uid, data, instruction) = self.generate_data_instruction_for_constant(expression)
        list_to_add_to.append(instruction)
        if(not self.is_type_default(data[0])):
            self.constants.append((uid, data))
        if(tail):
            list_to_add_to.append((OppCodes.ret, None))


    def compile_if(self, list_to_add_to, expression, tail):
        """Compile an SIF

        Args:
            list_to_add_to (List): The list to add the instructions to
            expression (SIf): SIf expression to compile
            tail (boolean): Is expression in tail position
        """
        if(not isinstance(expression, SIf)):
            raise SynError("Not an SIf expression, instead of type: " + str(type(expression)))

        # Compile the test in non tail position
        self.compile_expression(list_to_add_to, expression.test, False)
        false_branch_uid = self.generate_uid()
        if_end_branch_uid = self.generate_uid()
        list_to_add_to.append((OppCodes.if_false_branch, false_branch_uid))
        # Compile the consequent
        self.compile_expression(list_to_add_to, expression.consequent, tail)
        list_to_add_to.append((OppCodes.branch, if_end_branch_uid))
        list_to_add_to.append((OppCodes.label, false_branch_uid))
        # Compile the alternative
        self.compile_expression(list_to_add_to, expression.alternative, tail)
        list_to_add_to.append((OppCodes.label, if_end_branch_uid))


    def compile_lambda(self, list_to_add_to, expression, tail):
        """Compile a lambda procedure

        Args:
            list_to_add_to (List): The list to add the instructions to
            expression (SIf): SLambda expression to compile
            tail (boolean): Is expression in tail position
        """
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
        """Compile a list of expressions

        Args:
            list_to_add_to (List): The list to add the instructions to
            sequence (List): The sequence to compile 
            tail (boolean): Is expression in tail position
        """
        # Compile all the expressions in the sequence in the non tail position except the last one, the
        # last one inherits the tail argument
        len_sequence = len(sequence)
        for i in range(len_sequence - 1):
            self.compile_expression(list_to_add_to, sequence[i], False)
        if(len_sequence != 0):
            self.compile_expression(list_to_add_to, sequence[len_sequence - 1], tail)


    def compile_variable(self, list_to_add_to, expression, tail):
        """Compile a variable, insert a return statement if in tail position

        Args:
            list_to_add_to (List): The list to add the instructions to
            expression (SVariable): The variable to compile 
            tail (boolean): Is expression in tail position
        """
        if(not isinstance(expression, SVariable)):
            raise SynError("Not an SVariable expression, instead of type: " + str(type(expression)))
        list_to_add_to.append((OppCodes.lookup, expression.value))
        if(tail):
            list_to_add_to.append((OppCodes.ret, None))


    def compile_arguments(self, list_to_add_to, arguments, tail=False):
        """Compile arguments to a function call, all the arguments will always be
        compiled in non tail position.

        Args:
            list_to_add_to (List): The list to add the instructions to
            arguments (List): The list of expressions to compile 
            tail (boolean): Can never be True, only present for consistency purposes
        """
        if(tail):
            raise SynError("Tail should always be false when compiling arguments")
        for arg in arguments[::-1]:
            self.compile_expression(list_to_add_to, arg, False)
            list_to_add_to.append((OppCodes.push, None))


    def compile_proc_application(self, list_to_add_to, expression, tail):
        """Compile a procedure application

        Args:
            list_to_add_to (List): The list to add the instructions to
            expression (SProcApplication): The procedure application to compile 
            tail (boolean): Is expression in tail position
        """
        if(not isinstance(expression, SProcApplication)):
            raise SynError("Not an SProcApplication expression, instead of type: " + str(type(expression)))
        uid = None
        # If not in tail, then save a continuation before making the procedure call
        if(not tail):
            uid = self.generate_uid()
            list_to_add_to.append((OppCodes.save_continuation, uid))
            
        # Compile the arguments
        self.compile_arguments(list_to_add_to, expression.operands, False)
        # Compile the operator
        self.compile_expression(list_to_add_to, expression.operator, False)
        list_to_add_to.append((OppCodes.apply, None))

        if(not tail):
            list_to_add_to.append((OppCodes.label, uid))


    def compile_define(self, list_to_add_to, expression, tail):
        """Compile a SDefine special form

        Args:
            list_to_add_to (List): The list to add the instructions to
            expression (SDefine): The define special form to compile 
            tail (boolean): Can never be tail, defines are always top level. Present for consistency reasons
        """
        # Define should always be a top level expression
        if(tail):
            raise SynError("Define in tail posisiton, not allowed")
        if(not isinstance(expression, SDefine)):
            raise SynError("Expression is not of type SDefine, instead is of type " + str(type(expression)))
        self.compile_expression(list_to_add_to, expression.expression, False)
        list_to_add_to.append((OppCodes.define, str(expression.var)))


    def compile_set(self, list_to_add_to, expression, tail):
        """Compile SSet special form

        Args:
            list_to_add_to (List): The list to add the instructions to
            expression (SSet): The set special form to compile 
            tail (boolean): Is expression in tail position
        """
        if(not isinstance(expression, SSet)):
            raise SynError("Expression is not of type SSet, instead is of type " + str(type(expression)))
        # Compute the argument to set in non tail position
        self.compile_expression(list_to_add_to, expression.expression, False)
        list_to_add_to.append((OppCodes.set, expression.variable.value))
        if(tail):
            list_to_add_to.append((OppCodes.ret, None))


    def compile_and(self, list_to_add_to, expression, tail):
        """Compile SAnd special form

        Args:
            list_to_add_to (List): The list to add the instructions to
            expression (SAnd): The and special form to compile 
            tail (boolean): Is expression in tail position
        """
        if(not isinstance(expression, SAnd)):
            raise SynError("Expression is not of type SAnd, instead is of type " + str(type(expression)))
        and_false_uid = self.generate_uid()
        and_end_uid = self.generate_uid()
        for exp in expression.expressions:
            self.compile_expression(list_to_add_to, exp, False)
            # Allow false short-circuiting
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
        """Compile SOr special form

        Args:
            list_to_add_to (List): The list to add the instructions to
            expression (SOr): The or special form to compile 
            tail (boolean): Is expression in tail position
        """
        if(not isinstance(expression, SOr)):
            raise SynError("Expression is not of type SOr, instead is of type " + str(type(expression)))
        or_true_uid = self.generate_uid()
        or_end_uid = self.generate_uid()

        for exp in expression.expressions:
            self.compile_expression(list_to_add_to, exp, False)
            # Allow true short-cirtuiting
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
        """Compile let special form

        Args:
            list_to_add_to (List): The list to add the instructions to
            expression (SLet): The or special form to compile 
            tail (boolean): Is expression in tail position
        """
        if(not isinstance(expression, SLet)):
            raise SynError("Expression is not of type SLet, instead is of type " + str(type(expression)))
        bindings = [x[1] for x in expression.var_bindings]
        vars = [x[0] for x in expression.var_bindings]
        vars = list(map(str, vars))
        self.compile_arguments(list_to_add_to, bindings, False)
        list_to_add_to.append((OppCodes.bind, vars))
        self.compile_sequence(list_to_add_to, expression.body, tail)
        list_to_add_to.append((OppCodes.unbind, None))


    def compile_expression(self, list_to_add_to,  expression, tail):
        """Compile a scheme expression

        Args:
            list_to_add_to (List): The list to add the instructions to
            expression (SExpression): Expression to compile
            tail (boolean): Is expression in tail position
        """
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
        """Compile the input AST
        """
        for exp in self.ast:
            # All top level expressions are always in non tail position
            self.compile_expression(self.instructions, exp, False)
        self.instructions.append((OppCodes.ext, None))
        return(self.constants, self.instructions, self.procedures)


    def debug_output(self):
        """Produce human readable compiled version
        Returns:
            string: The human readable compiled version
        """
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

        return output


if __name__ == "__main__":

    def print_help():
        print("Usage: python3 compiler.py -i <input_file> -o <output_file>")
        print("Optional arguments:")
        print("\t1) To generate compiled code in human readable form: -c <file_name>")
        print("\t2) To generate assembled code in human readable form: -a <file_name>")

    compiled_human_readable = False
    assembled_human_readable = False
    compiled_verbose = None
    assembled_verbose = None
    input_file = None
    output_file = None

    opts, args = getopt.getopt(sys.argv[1:], "i:o:c:a:h", [])
    for opt, arg in opts:
        if(opt == "-i"):
            input_file = arg
        elif(opt == "-h"):
            print_help()
        elif(opt == "-o"):
            output_file = arg
        elif(opt == "-c"):
            compiled_human_readable = True
            compiled_verbose = arg
        elif(opt == "-a"):
            assembled_human_readable = True
            assembled_verbose = arg
        else:
            print("invlid argument", opt)
            print_help()
            exit(1)

    if((not input_file) or (not output_file)):
        print_help()
        exit(1)

    with open(input_file) as file_name:
        code = file_name.read()
    ast_generator = ASTGenerator(code)
    ast = ast_generator.generate_ast()

    compiler = Compiler(ast)
    (constants, main, procedures) = compiler.compile()
    if(compiled_human_readable):
        with open(compiled_verbose, "w") as compiled_verbose_out:
            compiled_verbose_out.write(compiler.debug_output())

    assembler = Assembler(constants, main, procedures)
    assembled = assembler.assemble()
    with open(output_file, "wb") as out_file:
        out_file.write(assembled)

    if(assembled_human_readable):
        with open(assembled_verbose, "w") as assembled_verbose_out:
            assembled_verbose_out.write(assembler.debug_output())
