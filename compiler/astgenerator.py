from expressions import *

class ASTGenerator:


    def __init__(self, code):
        """ASTGenerator constructor

        Args:
            code (str): The scheme code
        """
        self.code = code
        self.code_len = len(code)
        self.current = 0
        self.tokens = []


    def report(self, loc, msg):
        """Raise syntax error

        Args:
            loc (int): The location of the error
            msg (str): String to print to the user
        """
        class SynError(Exception):
            def __init__(self, message):
                super().__init__(message)

            def __str__(self):
                return f"Error: {self.args[0]}"

        start = loc

        # Find the 'line' the loc belongs to
        while(start > 0 and self.code[start] != '\n'):
            start -= 1
        if(self.code[start] == "\n"):
            start += 1
        end = loc
        while(end < self.code_len and self.code[end] != '\n'):
            end += 1

        # Print the line of code where error occurs and add a helpful guide to pin point the loc
        string = self.code[start:end]
        print(string)
        for i in range(loc - start):
            print("_", end = "")
        print("/")
        a =  SynError("Error at character " + str(loc) + ": " + msg)
        print(a)
        exit(1)


    def __str__(self):
        return self.code
    

    def consume_number_from(self, start, until=None):
        """Consume a scheme number

        Args:
            start (int): The index where the number begins
            until (int, optional): Defaults to None.

        Returns:
            int: The number converted into a float
        """
        start_backup = start
        eof = self.code_len if until == None else until
        # Consume until whitespace or eof
        while((not start >= eof) and (not self.code[start].isspace())):
            start += 1
        float_str = self.code[start_backup:start] 
        try:
            float(float_str)
            return start
        except:
            self.report(start_backup, repr(float_str) + " is not a number")
    

    def consume_string_from(self, start, until=None):
        """Consume a scheme string

        Args:
            start (int): The index of the first single quote
            until (int, optional): Defaults to None.

        Returns:
            int: The index after the string ends
        """
        eof = self.code_len if until == None else until
        start += 1
        while(True):
            if(start >= eof):
                self.report(start, "missing quotes for a string")
            if(self.code[start] == '"'):
                return start + 1
            else:
                start += 1
    

    def consume_boolean_from(self, start, until=None):
        """Consume a scheme boolean

        Args:
            start (int): The location of #
            until (int, optional): Defaults to None.

        Returns:
            int: The index after the boolean ends
        """
        eof = self.code_len if until == None else until
        start += 1
        if(start >= eof):
            self.report(start, "invalid boolean")
        if(not (self.code[start] == "f" or self.code[start] == "t")):
            self.report(start, "boolean can either be #t or #f")
        return start + 1
    

    def consume_word_from(self, start, until=None):
        """Consume an english word, reports an error when the word contains parenthesis

        Args:
            start (int): The index where the word begins
            until (int, optional): Defaults to None.

        Returns:
            int: The index after the word ends
        """
        eof = self.code_len if until == None else until
        while(True):
            if(start >= eof):
                return start
            if(self.code[start] == '(' or self.code[start] == ')'):
                self.report(start, "Unpected " + self.code[start])
            if(not self.code[start].isspace()):
                start += 1
            else:
                return start


    def consume_word_from_without_error(self, start, until=None):
        """Consume an english word, DOES NOT report an error when the word contains parenthesis

        Args:
            start (int): The index where the word begins
            until (int, optional): Defaults to None.

        Returns:
            int: The index after the word ends
        """
        eof = self.code_len if until == None else until
        while(True):
            if(start >= eof):
                return start
            if(not self.code[start].isspace()):
                start += 1
            else:
                return start


    def consume_var_from(self, start, until=None):
        """Consume a scheme variable

        Args:
            start (int): The index where the variable begins
            until (int, optional): Defaults to None.

        Returns:
            int: The index after the variable ends
        """
        eof = self.code_len if until == None else until
        if(start >= eof):
            return start
        if(not self.code[start].isalpha()):
            self.report(start, "Variable does not start with an alphabet")
        while(True):
            if(start >= eof):
                return start
            if(not self.code[start].isspace()):
                start += 1
            else:
                return start


    def consume_parenthesis_from(self, start, until=None):
        """Consume a scheme parenthesis

        Args:
            start (int): The index where '(' is present
            until (int, optional): Defaults to None.

        Returns:
            int: The index after the matching ')'
        """
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
        """Is scheme special form

        Args:
            str (str): The word to check

        Returns:
            boolean: True if str is a special form
        """
        return str in ["quote", "lambda", "if", "and", "or", "let", "set!", "begin", "define", "cond"]


    def is_built_in_func(self, str):
        """Is scheme built in function

        Args:
            str (str): The word to check

        Returns:
            boolean: True if str is a built in function that should not be re-named
        """
        return str in ["cons", "car", "cdr", "list", "string?", "pair?", "symbol?", "integer?", "eq?", "equal?", "eqv?"]


    def consume_and_process_expressions(self, start, end):
        """Consume and process multiple scheme expressions

        Args:
            start (int): The index to start at
            end (int): The index to end at

        Returns:
            List: List of scheme expressions
        """
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
        """Generate a SLambda object

        Args:
            start (int): The start of the special form body
            end (int): The end of the special form body, this is the index of the special form's ')'

        Returns:
            SLambda: The processed SLambda object
        """
        (variables_start, variables_end) = self.consume_expression(start, end)
        if(variables_end == None):
            self.report(start, "no bound variable list in lambda function")
        # This is to make sure we have parenthesis around the variable bound list
        if(not ((self.code[variables_start] == '(') and (self.code[variables_end-1] == ')'))):
            raise self.report(variables_start, "bound variable list not in proper format. Make sure the variables are enclosed in parenthesis")
        # Make sure every expression in the variable bound list is a variable
        variable_list = self.consume_and_process_expressions(variables_start + 1, variables_end - 1)
        for var in variable_list:
            if(not isinstance(var, SVariable)):
                self.report(variables_start, "not all members of bound variable list are variables")
        body = self.consume_and_process_expressions(variables_end, end)
        if(len(body) == 0):
            self.report(variables_end, "no body in lambda expression")
        return SLambda(variable_list, body)


    def dispach_if(self, start, end):
        """Generate a SIf object

        Args:
            start (int): The start of the special form body
            end (int): The end of the special form body, this is the index of the special form's ')'

        Returns:
            SIf: The processed SIF object
        """
        (test_start, test_end) = self.consume_expression(start, end)
        if(test_end == None):
            self.report(start, "no test inside if")
        test = self.process_expression(test_start, test_end)

        (consequent_start, consequent_end) = self.consume_expression(test_end, end)
        if(consequent_end == None):
            self.report(start, "no consequent inside if")
        consequent = self.process_expression(consequent_start, consequent_end)

        (alternative_start, alternative_end) = self.consume_expression(consequent_end, end)
        if(alternative_end == None):
            self.report(start, "no alternative inside if")
        alternative = self.process_expression(alternative_start, alternative_end)

        # Try consuming one more expression to see if the IF statement has more than 3 expressions in it
        nxt, nxt_end = self.consume_expression(alternative_end, end)
        if(nxt_end != None):
            self.report(alternative_end, "if contains more expressions than the required number (3)")
        return SIf(test, consequent, alternative) 


    def dispach_cond(self, start, end):
        """Generate a scheme cond by repurposing SIf

        Args:
            start (int): The start of the special form body
            end (int): The end of the special form body, this is the index of the special form's ')'

        Returns:
            SIf: The processed cond as an SIf
        """
        test_action_pairs = self.consume_and_process_expressions(start, end)

        if(len(test_action_pairs) == 0):
            self.report(start, "cond should contain atleast one test action pair")

        # Every pair should be a SProcApplication, with the test being the operator and the actions being the operands
        for pair in test_action_pairs:
            if(not isinstance(pair, SProcApplication)):
                self.report(start, "improper let")

        # Making sure that else branch is always the last one
        for i in range(len(test_action_pairs) - 1):
            if(isinstance(test_action_pairs[i].operator, SVariable)):
                if(test_action_pairs[i].operator.value == "else"):
                    self.report(start, "else should be the last branch in a cond")
                    
        # Check if the last branch is else, initialize cur appropriately
        cur = SBool("#f")
        else_present = False
        if(isinstance(test_action_pairs[-1].operator, SVariable)):
            if(test_action_pairs[-1].operator.value == "else"):
                else_present = True
                cur = SIf(SBool("#t"), SBegin(test_action_pairs[-1].operands), cur)
        
        # As we have already set up the value of cur, ignore the last branch if its an else
        pairs = test_action_pairs[:-1] if else_present else test_action_pairs
        reversed_pairs = pairs[::-1]
        # Built up the If using the reversed list
        for pair in reversed_pairs:
            cur = SIf(pair.operator, SBegin(pair.operands), cur)
        return cur
        

    # start is the special form end
    def dispach_let(self, start, end):
        """Generate a SLet

        Args:
            start (int): The start of the special form body
            end (int): The end of the special form body, this is the index of the special form's ')'

        Returns:
            SLet: The processed SLet
        """
        var_bindings_start, var_bindings_end = self.consume_expression(start, end)
        if(var_bindings_end == None):
            self.report(start, "empty let")

        # The call below will return SProcedureApplications, re-purpose them for the let variable bindings
        bindings = self.consume_and_process_expressions(var_bindings_start + 1, var_bindings_end - 1)
        if(len(bindings) < 1):
            self.report(var_bindings_start, "improper let, should have atleast one variable binding")
        var_bindings = []

        # Go through each binding, and generate a tuple of (variable, expression)
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

        # Process the body of the let
        expressions = self.consume_and_process_expressions(var_bindings_end, end)
        if(len(expressions) == 0):
            self.report(var_bindings_end, "improper let, the body should contain atleast one expression")
        return SLet(var_bindings, expressions)


    def process_quote(self, start, end, process_list=False):
        """Process a scheme quote.

        Args:
            start (int): The start of the special form body
            end (int): The end of the special form body, this is the index of the special form's ')'
            process_list (boolean): True if we are inside a quoted list and need to consume multiple quotes. Defaults to False
        Returns:
            SExpression: Could be a const list, or a symbol or any other scheme constant
        """
        if(process_list):
            exp_start, exp_end = self.consume_expression(start, end)
            # If no expression found, then the list we are processing is an empty list
            if(exp_end == None):
                return None
            list_objs = []
            while(True):
                if(exp_start == None):
                    return SConstList(list_objs)
                if(self.code[exp_start] == '('):
                    # we need to process a list
                    list_obj = self.process_quote(exp_start+1, exp_end-1, process_list=True)
                    if(list_obj == None):
                        list_objs.append(SEmptyList())
                    else:
                        list_objs.append(list_obj)
                else:
                    # Repurpose the SVariable to be a SSymbol
                    exp = self.process_expression(exp_start, exp_end)
                    if(isinstance(exp, SVariable)):
                        exp = SSymbol(exp.value)
                    list_objs.append(exp)
                exp_start, exp_end = self.consume_expression(exp_end, end)
        else:
            # At this point we don't know if it's a list or not
            exp_start, exp_end = self.consume_expression(start, end)
            if(exp_end == None):
                self.report(start, "improper quote, quote needs atleast one argument")
            second_exp_start, second_exp_end = self.consume_expression(exp_end, end)
            if(second_exp_end != None):
                self.report(second_exp_start, "improper quote, quote only takes one argument")
            if(self.code[exp_start] == '('):
                ans = self.process_quote(exp_start+1, exp_end-1, process_list=True)
                if(ans == None):
                    return SEmptyList()
                return ans
            else:
                exp = self.process_expression(exp_start, exp_end)
                # Repurpose this single SVariable as SSymbol
                if(isinstance(exp, SVariable)):
                    exp = SSymbol(exp.value)
                return exp


    def dispach_special_form(self, start, end):
        """Dispach on special form

        Args:
            start (int): The index AFTER special form's '('
            end (int): The index OF the special form's ')'

        Returns:
            SExpression: The dispached and processed special form
        """
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
        self.report(start, "not a special form. Compiler design error")


    # start is the ( and end is the character after )
    # When string sliced, this procedure can see the string it is trying to process
    def process_expression(self, start, end):
        """Process and generate SExpression

        Args:
            start (int): The index where the expression starts. The index where '(' is present if the expression is procedure application / special form
            end (int): The index where the expression ends. This is one AFTER the index where ')' is present if the expression is procedure application / special form

        Returns:
            SExpression: Returns the processed expression
        """
        c = self.code[start]
        if(self.is_numeric(start, end)):
            return SNumber(float(self.code[start:end]))
        # String
        elif(c == '"'):
            return SString(self.code[start+1:end-1])
        # Quotes
        elif(c == "'"):
            # TODO: add quotation functionality using '
            return None
        # Boolean
        elif(c == "#"):
            return SBool(self.code[start:end])
        # Special form or a procedure application
        elif(c == "("):

            first_word_start = self.ignore_whitespace(start+1)
            if(first_word_start == end):
                self.report(start, "empty parenthesis")

            first_word_end = self.consume_word_from_without_error(first_word_start, end - 1)
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
                operator = self.process_expression(operator_start, operator_end)
                
                # Process the operands
                operands = []
                previous_operand_end = operator_end
                while(True):
                    next_operand_start = self.ignore_whitespace(previous_operand_end, end - 1)
                    if(next_operand_start == None):
                        break
                    (x, next_operand_end) = self.consume_expression(next_operand_start, end - 1)
                    if(next_operand_end == None):
                        break
                    operand = self.process_expression(next_operand_start, next_operand_end)
                    operands.append(operand)
                    previous_operand_end = next_operand_end
                
                return SProcApplication(operator, operands)
        # Variable
        else:
            return SVariable(self.code[start:end])


    def ignore_whitespace(self, start, until=None):
        """Ignore whitespace

        Args:
            start (int): The index to start at
            until (int, optional): Defaults to None.

        Returns:
            int: The index that is a non white space character
        """
        eof = self.code_len if until == None else until
        while(True):
            if(start >= eof):
                return None
            if(self.code[start].isspace()):
                start += 1
            else:
                return start


    def is_numeric(self, start, until=None):
        """Check if start points to the start of a scheme number

        Args:
            start (int): The index where we suspect the number begins
            until (int, optional): Defaults to None.

        Returns:
            boolean: True if it's a potential start to a scheme number
        """
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


    def consume_expression(self, start, until=None):
        """Consume expression, this function tells us how to read an expression as a string

        Args:
            start (int): The start of the expression
            until (int, optional): Defaults to None.

        Returns:
            (start, next_start): The tuple where start is the start of the expression and next_start is the index where the next expression could potentially start
        """
        
        start = self.ignore_whitespace(start, until)
        if(start == None):
            return (None, None)
        c = self.code[start]

        # Number
        if(self.is_numeric(start, until)):
            next_start = self.consume_number_from(start, until)
            return (start, next_start)
        # String
        elif(c == '"'):
            next_start = self.consume_string_from(start, until)
            return (start, next_start)
        # Quotes
        elif(c == "'"):
            next_start = self.consume_parenthesis_from(start + 1, until)
            return (start, next_start)
        # Boolean
        elif(c == "#"):
            next_start = self.consume_boolean_from(start, until)
            return (start, next_start)
        # Expression
        elif(c == "("):
            next_start = self.consume_parenthesis_from(start, until)
            return (start, next_start)
        # Variable (Either user defined or built in)
        else:
            next_start = self.consume_word_from(start, until)
            return (start, next_start)
    

    def generate_ast(self):
        """Generate AST for the input code

        Returns:
            List: List of SExpression
        """
        return self.consume_and_process_expressions(0, self.code_len)
