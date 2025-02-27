from expressions import *

class SynError(Exception):
    def __init__(self, message):
        super().__init__(message)

    def __str__(self):
        return f"Error: {self.args[0]}"

class ASTGenerator:

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
        return str in ["quote", "lambda", "if", "and", "or", "let", "set!", "begin", "define", "cond"]

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
    
    def dispach_cond(self, start, end):
        test_action_pairs = self.consume_and_process_expressions(start, end)

        if(len(test_action_pairs) == 0):
            self.report(start, "cond should contain atleast one test action pair")

        # Every pair should be a procapplication, with the test being the operator and the actions being the operands
        for pair in test_action_pairs:
            if(not isinstance(pair, SProcApplication)):
                self.report(start, "Improper let")

        for i in range(len(test_action_pairs) - 1):
            if(isinstance(test_action_pairs[i].operator, SVariable)):
                if(test_action_pairs[i].operator.value == "equal"):
                    self.report(start, "equal should be the last branch in a cond")
                    
        cur = SBool("#f")
        else_present = False
        if(isinstance(test_action_pairs[-1].operator, SVariable)):
            if(test_action_pairs[-1].operator.value == "else"):
                else_present = True
                cur = SIf(SBool("#t"), SBegin(test_action_pairs[-1].operands), cur)
        
        reversed_pairs = test_action_pairs[:-1] if else_present else test_action_pairs
        reversed_pairs = reversed_pairs[::-1]
        for pair in reversed_pairs:
            cur = SIf(pair.operator, SBegin(pair.operands), cur)
        
        return cur
        
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
            if(self.is_built_in_func(str(var))):
                self.report(special_form_end, "cannot set the value of a built in function")
            if(not isinstance(var, SVariable)):
                self.report(special_form_end, "first argument to define should be a variable")
            exp = define_expressions[1]
            if(not isinstance(exp, Expression)):
                self.report(special_form_end, "second arguemnt to define should be a scheme expression")
            return SDefine(var, exp)
        if(special_form == "cond"):
            return self.dispach_cond(special_form_end, end)
        
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
            return SString(self.code[start+1:end-1])
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
    
    def generate_ast(self):
        return self.consume_and_process_expressions(0, self.code_len)