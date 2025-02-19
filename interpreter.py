import sys
from expressions import *
from compilerenums import *

class SynError(Exception):
    def __init__(self, message):
        super().__init__(message)

    def __str__(self):
        return f"Error: {self.args[0]}"

class ASTGen:

    def __init__(self, code):
        self.code = code
        self.code_len = len(code)
        self.current = 0
        self.tokens = []

    def report(self, char, msg):
        start = char
        while(start > 0 and self.code[start] != '\n'):
            start -= 1
        if(self.code[start] == "\n"):
            start += 1
        end = char
        while(end < self.code_len and self.code[end] != '\n'):
            end += 1
        string = self.code[start:end]
        print(string)
        for i in range(char - start):
            print("_", end = "")
        print("/")
        a =  SynError("Error at character " + str(char) + ": " + msg)
        print(a)
        exit(1)

    def __str__(self):
        return self.code
    
    def consume_number_from(self, start, until=None):
        start_backup = start
        eof = self.code_len if until == None else until
        while((not start >= eof) and (not self.code[start].isspace())):
            start += 1
        float_str = self.code[start_backup:start] 
        try:
            float(float_str)
            return start
        except:
            self.report(start_backup, repr(float_str) + " is not a number")
    
    def consume_string_from(self, start, until=None):
        # as start is at ", move one place forward
        eof = self.code_len if until == None else until
        start += 1
        while(True):
            if(start >= eof):
                raise SynError("Error at character " + str(start) + ". Missing ending quotes for string")
            if(self.code[start] == '"'):
                return start + 1
            else:
                start += 1
    
    def consume_boolean_from(self, start, until=None):
        eof = self.code_len if until == None else until
        start += 1
        if(start >= eof):
            raise SynError("Error at character " + str(start) + ", Invalid boolean")
        if(not (self.code[start] == "f" or self.code[start] == "t")):
            raise SynError("Error at character " + str(start) + ", Invalid boolean value #" + self.code[start])
        return start + 1
    
    def consume_word_from(self, start, until=None):
        eof = self.code_len if until == None else until
        while(True):
            if(start >= eof):
                return start
            if(self.code[start] == '(' or self.code[start] == ')'):
                raise SynError("Error at " + str(start) + ", Unpected " + self.code[start])
            if(not self.code[start].isspace()):
                start += 1
            else:
                return start

    def consume_word_from_without_error(self, start, until=None):
        eof = self.code_len if until == None else until
        while(True):
            if(start >= eof):
                return start
            if(not self.code[start].isspace()):
                start += 1
            else:
                return start

    def consume_var_from(self, start, until=None):
        eof = self.code_len if until == None else until
        if(start >= eof):
            return start
        if(not self.code[start].isalpha()):
            raise SynError("Error at character " + str(start) + ", variable does not start with an alphabet")
        while(True):
            if(start >= eof):
                return start
            if(not self.code[start].isspace()):
                start += 1
            else:
                return start

    def consume_parenthesis_from(self, start, until=None):
        start_backup = start
        eof = self.code_len if until == None else until
        left_brackets_no = 1
        start += 1
        while(True):
            if(start >= eof):
                self.report(start_backup, "Missing closing bracket")
            elif(self.code[start] == '('):
                left_brackets_no += 1
            elif(self.code[start] == ')'):
                if(left_brackets_no == 1):
                    start += 1
                    return start
                else:
                    left_brackets_no -= 1
            start += 1
    
    def is_special_form(self, str):
        return str in ["quote", "lambda", "if", "and", "or", "let", "set!", "begin", "define"]

    def is_built_in_func(self, str):
        return str in ["cons", "car", "cdr", "list", "string?", "pair?", "symbol?", "integer?", "eq?", "equal?", "eqv?"]

    def consume_and_process_expressions(self, start, end):
        # consume multiple expression from start till the end, and return the list
        expressions = []
        (expression_start, expression_end) = self.consume_expression(start, end)
        while(expression_end != None):
            expression = self.process_expression(expression_start, expression_end)
            expressions.append(expression)
            start = expression_end
            (expression_start, expression_end) = self.consume_expression(start, end)
        return expressions

    def dispach_lambda(self, start, end):
        (variables_start, variables_end) = self.consume_expression(start, end)
        if(variables_end == None):
            raise SynError("Error at " + str(start) + " no bound variable list")
        # This is to make sure we have parenthesis around the variable bound list
        if(not ((self.code[variables_start] == '(') and (self.code[variables_end-1] == ')'))):
            raise SynError("Error at " + str(variables_start) + ", bound variable list not in proper format. Make sure the variables are enclosed in parenthesis")
        # Make sure every expression in the variable bound list is a variable
        variable_list = self.consume_and_process_expressions(variables_start + 1, variables_end - 1)
        for var in variable_list:
            if(not isinstance(var, SVariable)):
                raise SynError("Error at " + str(variables_start) + " not all members of bound variable list are variables")
        body = self.consume_and_process_expressions(variables_end, end)
        if(len(body) == 0):
            raise SynError("Error at " + str(variables_end)+ " no body in lambda expression")
        return SLambda(variable_list, body)

    def dispach_if(self, start, end):
        (test_start, test_end) = self.consume_expression(start, end)
        if(test_end == None):
            raise SynError("Error at " + str(start) + ", no test for 'if' special form")
        test = self.process_expression(test_start, test_end)
        (consequent_start, consequent_end) = self.consume_expression(test_end, end)
        if(consequent_end == None):
            raise SynError("Error at " + str(start) + ", no consequent for 'if' special form")
        consequent = self.process_expression(consequent_start, consequent_end)
        (alternative_start, alternative_end) = self.consume_expression(consequent_end, end)
        if(alternative_end == None):
            raise SynError("Error at " + str(start) + ", no alternative for 'if' special form")
        alternative = self.process_expression(alternative_start, alternative_end)
        # Try consuming one more expression to see if the IF statement has more than 3 expressions in it
        nxt, nxt_end = self.consume_expression(alternative_end, end)
        if(nxt_end != None):
            raise SynError("Error at " + str(alternative_end) + ", If contains more expressions than required")
        return SIf(test, consequent, alternative) 
    
    # start is the special form end
    def dispach_let(self, start, end):
        var_bindings_start, var_bindings_end = self.consume_expression(start, end)
        # Empty let
        if(var_bindings_end == None):
            self.report(start, "improper let")
        # The call below will return SProcedureApplications, re-purpose them for the let variable bindings
        bindings = self.consume_and_process_expressions(var_bindings_start + 1, var_bindings_end - 1)
        if(len(bindings) < 1):
            self.report(var_bindings_start, "improper let, should have atleast one variable binding")
        var_bindings = []
        for binding in bindings:
            if(not isinstance(binding, SProcApplication)):
                self.report(var_bindings_start, "improper let, the let variable bindings should of of form ((<variable> <expression)...)")
            var = binding.operator
            if(self.is_built_in_func(var)):
                self.report(var_bindings_start, "improper let, cannot redefine built in functions")
            if(not isinstance(var, SVariable)):
                self.report(var_bindings_start, "improper let, can only bind expressions to variables")
            exp = binding.operands
            if(len(exp) != 1):
                self.report(var_bindings_start, "improper let, every variable binding should have one expression")
            exp = exp[0]
            var_bindings.append((var, exp))

        # extract the sequence of expressions
        # let_body_start, let_body_end = self.consume_expression(var_bindings_end, end)
        # if(let_body_end == None):
        #     self.report(let_body_start, "improper let, should have the let body")
        # if(not self.code[let_body_start] == '('):
        #     self.report(let_body_start, "improper let, missing (")
        # expressions = self.consume_and_process_expressions(let_body_start + 1, let_body_end - 1)

        expressions = self.consume_and_process_expressions(var_bindings_end, end)
        if(len(expressions) == 0):
            self.report(var_bindings_end, "improper let, the body should contain atleast one expression")

        return SLet(var_bindings, expressions)

    # In order to use functions process and consume expression, I've had to get a little creative with process_quote
    # Pass with process_multiple=True if you want to process a scheme list
    def process_quote(self, start, end, process_multiple=False):
        if(process_multiple):
            exp_start, exp_end = self.consume_expression(start, end)
            if(exp_end == None):
                return None
            quotes = []
            while(True):
                if(exp_start == None):
                    return SConstList(quotes)
                if(self.code[exp_start] == '('):
                    # we need to process a list
                    list_obj = self.process_quote(exp_start+1, exp_end-1, process_multiple=True)
                    if(list_obj == None):
                        quotes.append(SEmptyList())
                    else:
                        quotes.append(list_obj)
                else:
                    exp = self.process_expression(exp_start, exp_end)
                    if(isinstance(exp, SVariable)):
                        exp = SSymbol(exp.value)
                    quotes.append(exp)
                exp_start, exp_end = self.consume_expression(exp_end, end)
        else:
            # we only have to process a single thing
            exp_start, exp_end = self.consume_expression(start, end)
            if(exp_end == None):
                self.report(start, "improper quote, quote needs atleast one argument")
            second_exp_start, second_exp_end = self.consume_expression(exp_end, end)
            if(second_exp_end != None):
                self.report(second_exp_start, "improper quote, quote only takes one argument")
            if(self.code[exp_start] == '('):
                ans = self.process_quote(exp_start+1, exp_end-1, process_multiple=True)
                if(ans == None):
                    return SEmptyList()
                return ans
            else:
                exp = self.process_expression(exp_start, exp_end)
                if(isinstance(exp, SVariable)):
                    exp = SSymbol(exp.value)
                return exp

    # Given the start of the special form (where the first char of special form beigns) and the end is the pos of )
    # when sliced it can't see the ()'s
    def dispach_special_form(self, start, end):
        special_form_end = self.consume_word_from(start, end)
        special_form = self.code[start:special_form_end]
        if(special_form == "quote"):
            # Take in a list of variables, which might contain list in itself
            objs = self.process_quote(special_form_end, end)
            return objs
        if(special_form == "lambda"):
            return self.dispach_lambda(special_form_end, end)
        if(special_form == "if"):
            return self.dispach_if(special_form_end, end)
        if(special_form == "and"):
            # take in a a number of scheme expressions
            and_expressions = self.consume_and_process_expressions(special_form_end, end)
            return SAnd(and_expressions)
        if(special_form == "or"):
            # take in a a number of scheme expressions
            or_expressions = self.consume_and_process_expressions(special_form_end, end)
            return SOr(or_expressions)
        if(special_form == "let"):
            # take in a list of variable bindings and then a list of scheme expressions
            return self.dispach_let(special_form_end, end)
        if(special_form == "set!"):
            # take in a variable and an expression
            set_expressions = self.consume_and_process_expressions(special_form_end, end)
            if(len(set_expressions) != 2):
                self.report(special_form_end, "improper set, set should contain a variable and an single expression")
            if(not isinstance(set_expressions[0], SVariable)):
                self.report(special_form_end, "improper set, the first argument has to be a variable")
            if(not isinstance(set_expressions[1], Expression)):
                self.report(special_form_end, "improper set, the second argument has to be a variable")
            if(self.is_built_in_func(set_expressions[0].value)):
                self.report(special_form_end, "cannot set the value of a built in function")
            return SSet(set_expressions[0], set_expressions[1])
        # begin is not a special form
        if(special_form == "begin"):
            set_expressions = self.consume_and_process_expressions(special_form_end, end)
            return SBegin(set_expressions)
            # take in a number of scheme expressions
        if(special_form == "define"):
            define_expressions = self.consume_and_process_expressions(special_form_end, end)
            if(len(define_expressions) != 2):
                self.report(special_form_end, "define should only have 2 arguments")
            var = define_expressions[0]
            if(self.is_built_in_func(var)):
                self.report(special_form_end, "cannot set the value of a built in function")
            if(not isinstance(var, SVariable)):
                self.report(special_form_end, "first argument to define should be a variable")
            exp = define_expressions[1]
            if(not isinstance(exp, Expression)):
                self.report(special_form_end, "second arguemnt to define should be a scheme expression")
            return SDefine(var, exp)
        
    # start is the ( and end is the character after )
    # When string sliced, this procedure can see the string it is trying to process
    def process_expression(self, start, end):
        # print("processing expression: " + self.code[start:end])
        c = self.code[start]
        if(self.is_numeric(start, end)):
            # Create something of type number and then return it
            return SNumber(float(self.code[start:end]))
        # String
        elif(c == '"'):
            # Create something of type scheme string and return it
            return SString(self.code[start:end])
        # Quotes
        elif(c == "'"):
            # Create something of type scheme quote and return it
            return None
        # Boolean
        elif(c == "#"):
            return SBool(self.code[start:end])
        # Special form or a procedure application
        elif(c == "("):
            # Ignore whitespace to make sure that the <expression> actually contains something
            first_word_start = self.ignore_whitespace(start+1)
            if(first_word_start == end):
                raise SynError("Error at character " + str(start) + ", Empty parenthesis")
            # We know this expression contains something, extract the first word
            first_word_end = self.consume_word_from_without_error(first_word_start, end - 1)
            # Check to see if this word is a special form
            is_special_form = self.is_special_form(self.code[first_word_start: first_word_end])
            if(is_special_form):
                return self.dispach_special_form(first_word_start, end - 1)
            else:
                # This expression is a procedure application of the form (<operator> <operands>*)
                
                # Extract the operator
                operator_start = first_word_start
                (x, operator_end) = self.consume_expression(operator_start, end - 1)
                if(operator_end == None):
                    self.report(start, "improper procedure application")
                    # This is an expression with nothing in it
                operator = self.process_expression(operator_start, operator_end)
                
                # Process the operands
                operands = []
                previous_operand_end = operator_end
                while(True):
                    next_operand_start = self.ignore_whitespace(previous_operand_end, end - 1)
                    if(next_operand_start == None):
                        # print("no more operands to processss")
                        break
                    (x, next_operand_end) = self.consume_expression(next_operand_start, end - 1)
                    if(next_operand_end == None):
                        # print("no more operands to process")
                        break
                    operand = self.process_expression(next_operand_start, next_operand_end)
                    operands.append(operand)
                    previous_operand_end = next_operand_end
                
                return SProcApplication(operator, operands)


        # Variable
        else:
            return SVariable(self.code[start:end])
            
                    
    def ignore_whitespace(self, start, until=None):
        eof = self.code_len if until == None else until
        while(True):
            if(start >= eof):
                return None
            if(self.code[start].isspace()):
                start += 1
            else:
                return start

    def is_numeric(self, start, until=None):
        eof = self.code_len if until == None else until
        c = self.code[start]
        if(c.isnumeric()):
            return True
        elif(c == "-"):
            if(start+1 >= eof):
                return False
            elif(self.code[start+1].isnumeric()):
                return True
            else:
                return False

        
    # returns (string_expression, end)
    def consume_expression(self, start, until=None):
        # As each type of expression needs to deal with EOF in their own way, let's check for EOF only once here
        # and let the dispach functions deal with EOF in their own way
        
        start = self.ignore_whitespace(start, until)
        if(start == None):
            return (None, None)
        c = self.code[start]

        # Number
        if(self.is_numeric(start, until)):
            end = self.consume_number_from(start, until)
            return (start, end)
        # String
        elif(c == '"'):
            end = self.consume_string_from(start, until)
            return (start, end)
        # Quotes
        elif(c == "'"):
            end = self.consume_parenthesis_from(start + 1, until)
            return (start, end)
        # Boolean
        elif(c == "#"):
            end = self.consume_boolean_from(start, until)
            return (start, end)
        # Expression
        elif(c == "("):
            end = self.consume_parenthesis_from(start, until)
            return (start, end)
        # Variable (Either user defined or built in)
        else:
            end = self.consume_word_from(start, until)
            return (start, end)
    
    def produce_tokens(self):
        return self.consume_and_process_expressions(0, self.code_len)

class Compiler():
    def __init__(self, ast):
        self.ast = ast
        self.data = []
        self.label_prefixes = {}
        self.instructions = []
        # A list of tuple of (procedure_name, instructions)
        self.procedures = []
        self.symbols = set()
        # Reserve some initial cuid's, this way I can directly use them 
        self.cur_uid = len(Defaults)
    
    def generate_label(self, prefix):
        if(prefix in self.label_prefixes):
            self.label_prefixes[prefix] += 1
        else:
            self.label_prefixes[prefix] = 1
        return prefix + str(self.label_prefixes[prefix])
    
    def generate_uid(self):
        self.cur_uid += 1
        return self.cur_uid
        
    def is_type_default(self, exp):
        return isinstance(exp, Defaults)

    # just return the list of pre_requisite labels
    # add the pre_requisie data to self.data yourself
    def compile_list_constant(self, expression):
        if(not isinstance(expression, SConstList)):
            raise SynError(str(expression) + "is not a SConstList")
        consts = expression.consts
        consts_uids = []
        for exp in consts:
                (exp_uid, exp_data, _) = self.generate_data_instruction_for_constant(exp)
                consts_uids.append(exp_uid)
                if(not self.is_type_default(exp_data[0])):
                    self.data.append((exp_uid, exp_data))
                    
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
        # (label, data, instruction) = self.generate_data_instruction_for_constant(expression)
        (uid, data, instruction) = self.generate_data_instruction_for_constant(expression)
        list_to_add_to.append(instruction)
        # if(not isinstance(data, Defaults)):
        #     self.data.append((uid, data))
        if(not self.is_type_default(data[0])):
            self.data.append((uid, data))
        if(tail):
            list_to_add_to.append((OppCodes.ret, None))
        
    def compile_if(self, list_to_add_to, expression, tail):
        if(not isinstance(expression, SIf)):
            raise SynError("Not an SIf expression, instead of type: " + str(type(expression)))
        # Compile the test
        self.compile_expression(list_to_add_to, expression.test, False)
        # false_branch = self.generate_jump_label("if_false")
        # if_end_branch = self.generate_jump_label("if_end")
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
        # label = self.generate_jump_label("lambda")
        uid = self.generate_uid()
        var_bound_list_str = list(map(str, expression.bound_var_list))
        # ins.append("bind " + " ".join(var_bound_list_str))
        ins.append((OppCodes.bind, var_bound_list_str))
        self.compile_sequence(ins, expression.body, True)
        # list_to_add_to.append("make_closure " + label)
        list_to_add_to.append((OppCodes.make_closure, uid))
        if(tail):
            # list_to_add_to.append("return")
            list_to_add_to.append((OppCodes.ret, None))
        self.procedures.append((uid, ins))
       
    def compile_sequence(self, list_to_add_to, sequence, tail):
        len_sequence = len(sequence)
        # Compile all the first n-1 in non tail position
        for i in range(len_sequence - 1):
            self.compile_expression(list_to_add_to, sequence[i], False)
        # Compile the last one according to the argument given
        if(len_sequence != 0):
            self.compile_expression(list_to_add_to, sequence[len_sequence - 1], tail)
    
    def compile_variable(self, list_to_add_to, expression, tail):
        if(not isinstance(expression, SVariable)):
            raise SynError("Not an SVariable expression, instead of type: " + str(type(expression)))
        # list_to_add_to.append("lookup " + str(expression.value))
        list_to_add_to.append((OppCodes.lookup, expression.value))
        if(tail):
            list_to_add_to.append((OppCodes.ret, None))
    
    # the arguments are always in non tail position, so here tail should always be false
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
            # label = self.generate_jump_label("continuation") 
            # list_to_add_to.append("save_cont " + label)
            uid = self.generate_uid()
            list_to_add_to.append((OppCodes.save_continuation, uid))
            
        # Evaluate the arguments
        self.compile_arguments(list_to_add_to, expression.operands, False)
        self.compile_expression(list_to_add_to, expression.operator, False)
        # list_to_add_to.append("apply")
        list_to_add_to.append((OppCodes.apply, None))

        if(not tail):
            # list_to_add_to.append(label)
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
        # list_to_add_to.append("set " + str(expression.variable))
        list_to_add_to.append((OppCodes.set, expression.variable))
        if(tail):
            list_to_add_to.append("return")
    
    def compile_and(self, list_to_add_to, expression, tail):
        if(not isinstance(expression, SAnd)):
            raise SynError("Expression is not of type SAnd, instead is of type " + str(type(expression)))
        # and_false = self.generate_jump_label("and_false")
        and_false_uid = self.generate_uid()
        # and_end = self.generate_jump_label("and_end")
        and_end_uid = self.generate_uid()
        for exp in expression.expressions:
            self.compile_expression(list_to_add_to, exp, False)
            # list_to_add_to.append("if_false_branch " + and_false)
            list_to_add_to.append((OppCodes.if_false_branch, and_false_uid))
        # list_to_add_to.append("lookup bool_true")
        list_to_add_to.append((OppCodes.load_const, Defaults.boolean_true.value))
        if(tail):
            # list_to_add_to.append("return")
            list_to_add_to.append((OppCodes.ret, None))
        # list_to_add_to.append("jump " + and_end)
        list_to_add_to.append((OppCodes.branch, and_end_uid))
        # list_to_add_to.append(and_false)
        list_to_add_to.append((OppCodes.label, and_false_uid))
        # list_to_add_to.append("lookup bool_false")
        list_to_add_to.append((OppCodes.load_const, Defaults.boolean_false.value))

        if(tail):
            # list_to_add_to.append("return")
            list_to_add_to.append((OppCodes.ret, None))
        # list_to_add_to.append(and_end)
        list_to_add_to.append((OppCodes.label, and_end_uid))
            
    def compile_or(self, list_to_add_to, expression, tail):
        if(not isinstance(expression, SOr)):
            raise SynError("Expression is not of type SOr, instead is of type " + str(type(expression)))
        # or_true = self.generate_jump_label("or_true")
        or_true_uid = self.generate_uid()
        # or_end = self.generate_jump_label("or_end")
        or_end_uid = self.generate_uid()

        for exp in expression.expressions:
            self.compile_expression(list_to_add_to, exp, False)
            # list_to_add_to.append("if_true_branch " + or_true)
            list_to_add_to.append((OppCodes.if_true_branch, or_true_uid))
        # list_to_add_to.append("lookup bool_false")
        list_to_add_to.append((OppCodes.load_const, Defaults.boolean_false.value))
        if(tail):
            # list_to_add_to.append("return")
            list_to_add_to.append((OppCodes.ret, None))
        # list_to_add_to.append("jump " + or_end)
        list_to_add_to.append((OppCodes.branch, or_end_uid))
        # list_to_add_to.append(or_true)
        list_to_add_to.append((OppCodes.label, or_true_uid))
        # list_to_add_to.append("lookup bool_true")
        list_to_add_to.append((OppCodes.load_const, Defaults.boolean_true.value))
        if(tail):
            # list_to_add_to.append("return")
            list_to_add_to.append((OppCodes.ret, None))
        # list_to_add_to.append(or_end)
        list_to_add_to.append((OppCodes.label, or_end_uid))
        
    def compile_let(self, list_to_add_to, expression, tail):
        if(not isinstance(expression, SLet)):
            raise SynError("Expression is not of type SLet, instead is of type " + str(type(expression)))
        bindings = [x[1] for x in expression.var_bindings]
        vars = [x[0] for x in expression.var_bindings]
        vars = list(map(str, vars))
        self.compile_arguments(list_to_add_to, bindings, False)
        # list_to_add_to.append("bind " + " ".join(vars))
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
        for dat in self.data:
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
    filename = sys.argv[1]
    with open(filename) as file_name:
        code = file_name.read()
    ast_generator = ASTGen(code)
    tokens = ast_generator.produce_tokens()
    compiler = Compiler(tokens)
    compiler.compile()
    output = compiler.generate_human_readable()
    print(output, end='')

    


