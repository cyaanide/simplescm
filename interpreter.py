import sys
from expressions import *

class SynError(Exception):
    pass

class Interpreter:

    def __init__(self, code):
        self.code = code
        self.code_len = len(code)
        self.current = 0
        self.tokens = []

    def __str__(self):
        return self.code
    
    def consume_number_from(self, start, until=None):
        start_backup = start
        eof = self.code_len if until == None else until
        # while((not self.is_this_eof(start)) and (not self.code[start].isspace())):
        while((not start >= eof) and (not self.code[start].isspace())):
            start += 1
        float_str = self.code[start_backup:start] 
        try:
            float(float_str)
            return start
        except:
            raise SynError("Error at character " + str(start_backup) + ", " + repr(float_str) + " not a number")
    
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
    
    # def consume_word_from_until(self, start, end):
    #     if(start == end):
    #         return start
    #     while(True):
    #         # We have reached the boundry, return the word so far
    #         if(start == end - 1):
    #             return end
    #         if(not self.code[start].isspace()):
    #             start += 1
    #         else:
    #             return start

    def consume_word_from(self, start, until=None):
        eof = self.code_len if until == None else until
        while(True):
            if(start >= eof):
                return start
            if(not self.code[start].isspace()):
                start += 1
            else:
                return start

    def consume_parenthesis_from(self, start, until=None):
        eof = self.code_len if until == None else until
        left_brackets_no = 1
        start += 1
        while(True):
            if(start >= eof):
                raise SynError("Error at character " + str(start) + ". Missing closing bracket")
            elif(self.code[start] == '('):
                left_brackets_no += 1
            elif(self.code[start] == ')'):
                if(left_brackets_no == 1):
                    start += 1
                    return start
                else:
                    left_brackets_no -= 1
            start += 1
    
    def is_this_eof(self, x):
        return x >= self.code_len
    
    def is_special_form(self, str):
        print("checking to see if", str, "is a special form")
        return str in ["quote", "lambda", "if", "and", "or", "let", "set!", "begin"]

    # Given the start of the special form (where the first char of special form beigns) and the end is the pos of )
    # when sliced it can't see the ()'s
    def dispach_special_form(self, start, end):
        special_form_end = self.consume_word_from(start, end)
        special_form = self.code[start:special_form_end]
        if(special_form == "quote"):
            pass
        if(special_form == "lambda"):
            pass
        if(special_form == "if"):
            (test_start, test_end) = self.consume_expression(special_form_end, end)
            if(test_end == None):
                raise SynError("Error at " + str(special_form_end) + ", no test for 'if' special form")
            test = self.process_expression(test_start, test_end)
            (consequent_start, consequent_end) = self.consume_expression(test_end, end)
            if(consequent_end == None):
                raise SynError("Error at " + str(special_form_end) + ", no consequent for 'if' special form")
            consequent = self.process_expression(consequent_start, consequent_end)
            (alternative_start, alternative_end) = self.consume_expression(consequent_end, end)
            if(alternative_end == None):
                raise SynError("Error at " + str(special_form_end) + ", no alternative for 'if' special form")
            alternative = self.process_expression(alternative_start, alternative_end)
            return SIf(test, consequent, alternative) 
        if(special_form == "and"):
            pass
        if(special_form == "or"):
            pass
        if(special_form == "let"):
            pass
        if(special_form == "set!"):
            pass
        if(special_form == "begin"):
            pass
        

    
    # start is the ( and end is the character after )
    # When string sliced, this procedure can see the string it is trying to process
    def process_expression(self, start, end):
        print("processing expression: " + self.code[start:end])
        c = self.code[start]
        # Number
        if(c.isnumeric()):
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
            first_word_end = self.consume_word_from(first_word_start, end - 1)
            # Check to see if this word is a special form
            is_special_form = self.is_special_form(self.code[first_word_start: first_word_end])
            if(is_special_form):
                return self.dispach_special_form(first_word_start, end - 1)
            else:
                # This expression is a procedure application of the form (<operator> <operands>*)
                
                # Extract the operator
                operator_start = first_word_start
                (x, operator_end) = self.consume_expression(operator_start, end - 1)
                if(x != operator_start):
                    raise SynError("should never get here")
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


    # returns (string_expression, end)
    def consume_expression(self, start, until=None):
        # As each type of expression needs to deal with EOF in their own way, let's check for EOF only once here
        # and let the dispach functions deal with EOF in their own way
        
        start = self.ignore_whitespace(start, until)
        if(start == None):
            return (None, None)
        c = self.code[start]

        # Number
        if(c.isnumeric()):
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
        expressions = []
        (expression_start, expression_end) = self.consume_expression(self.current)
        while(expression_end != None):
            expression = self.process_expression(expression_start, expression_end)
            expressions.append(expression)
            self.current = expression_end
            (expression_start, expression_end) = self.consume_expression(self.current)
        return expressions

if __name__ == "__main__":
    filename = sys.argv[1]
    with open(filename) as file_name:
        code = file_name.read()
    interpreter = Interpreter(code)
    tokens = interpreter.produce_tokens()
    print(tokens)
    for i in tokens:
        print(type(i))
    



