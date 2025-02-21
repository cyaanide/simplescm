
class SError(Exception):
    pass

class Expression:
    def __init__(self):
        self.tail = None

class SConstant(Expression):
    pass

class SNumber(SConstant):
    def __init__(self, num):
        super().__init__()
        if(type(num) != float):
            raise SError("SNumber: not a float")
        self.value = num

    def __repr__(self):
        return str(self.value)

class SString(SConstant):
    def __init__(self, string):
        super().__init__()
        if(type(string) != str):
            raise SError("SString: not a string")
        self.value = string
    
    def __repr__(self):
        return str(self.value)
    
class SSymbol(SConstant):
    def __init__(self, string):
        super().__init__()
        if(type(string) != str):
            raise SError("SSymbol: not a string")
        self.value = string

    def __repr__(self):
        return "'" + self.value

class SBool(SConstant):
    def __init__(self, boolean):
        super().__init__()
        if(type(boolean) != str):
            raise SError("SBool: input is not a string")
        if(boolean == "#t"):
            self.value = True
        elif(boolean == "#f"):
            self.value = False
        else:
            raise SError("SBool: invalid input to the constructor")
    def __repr__(self):
        return str(self.value)

class SVariable(Expression):
    def __init__(self, string):
        super().__init__()
        if(type(string) != str):
            raise SError("SVariable: not a string")
        self.value = string
    
    def __repr__(self):
        return str(self.value)
    
class SEmptyList(SConstant):
    def __init__(self):
        super().__init__()
        pass

class SConstList(SConstant):
    def __init__(self, consts):
        super().__init__()
        self.consts = consts
    
    def __repr__(self):
        return "(SList: " + str(self.consts) + ")"

class SDefine(Expression):
    def __init__(self, var, expression):
        super().__init__()
        if(not isinstance(var, SVariable)):
            raise SError("SDefine: non variable in a define")
        if(not isinstance(expression, Expression)):
            raise SError("SDefine: second argument is not a scheme expression")
        self.var = var
        self.expression = expression
    
    def __repr__(self):
        return "(SDefine: " + str(self.var) + " " + str(self.expression) + ")"

class SLet(Expression):
    def __init__(self, var_bindings, body):
        super().__init__()
        for var_binding in var_bindings:
            if(not isinstance(var_binding[0], SVariable)):
                raise SError("SLet: non variable in a variable binding")
            if(not isinstance(var_binding[1], Expression)):
                raise SError("SLet: trying to bind a variable to a non expression")
        for exp in body:
            if(not isinstance(exp, Expression)):
                raise SError("SLet: non expression in let body")
        self.var_bindings = var_bindings
        self.body = body

    def __repr__(self):
        return "(SLet: VarBindings: " + str(self.var_bindings) + " Body: " + str(self.body) + ")"
        
class SIf(Expression):
    def __init__(self, test, consequent, alternative):
        super().__init__()
        if(not isinstance(test, Expression)):
            raise SError("SIf: test is not an instance of Expression")
        if(not isinstance(consequent, Expression)):
            raise SError("SIf: consequent is not an instance of Expression")
        if(not isinstance(alternative, Expression)):
            raise SError("SIf: alternative is not an instance of Expression")
        self.test = test
        self.consequent = consequent
        self.alternative = alternative
    
    def __repr__(self):
        return "(SIf " + str(self.test) + " " + str(self.consequent) + " " + str(self.alternative) +  ")"

class SProcApplication(Expression):
    def __init__(self, operator, operands):
        super().__init__()
        if(not isinstance(operator, Expression)):
            raise SError("SProcApplication: operator is not an instance of Expression")
        if(not isinstance(operands, list)):
            raise SError("SProcApplication: operands is not a list")
        for operand in operands:
            if(not isinstance(operand, Expression)):
                raise SError("SProcApplication: operand is not an instance of Expression")
        self.operator = operator
        self.operands = operands
        
    def __repr__(self):
        return "(SProcApplication " + str(self.operator) + " " + str(self.operands) + ")"
        
class SLambda(Expression):
    # Maybe add a check so that we can't add variable list that contains duplicates
    def __init__(self, bound_var_list, body):
        super().__init__()
        for var in bound_var_list:
            if(not isinstance(var, SVariable)):
                raise SError("SLambda: bound variable list is not a list of variables")
        self.bound_var_list = bound_var_list
        for exp in body:
            if(not isinstance(exp, Expression)):
                raise SError("SLambda: body is not a list of expressions")
        self.body = body
        
    def __repr__(self):
        return "(SLambda " + str(self.bound_var_list) + " " + str(self.body) + ")"

class SAnd(Expression):
    def __init__(self, expressions):
        super().__init__()
        for var in expressions:
            if(not isinstance(var, Expression)):
                raise SError("SAnd: Not all the arguments are exppressions")
        self.expressions = expressions
    
    def __repr__(self):
        return "(SAnd " + str(self.expressions) + ")"

class SOr(Expression):
    def __init__(self, expressions):
        super().__init__()
        for var in expressions:
            if(not isinstance(var, Expression)):
                raise SError("SOr: Not all the arguments are exppressions")
        self.expressions = expressions
    
    def __repr__(self):
        return "(SOr " + str(self.expressions) + ")"

class SSet(Expression):
    def __init__(self, variable, expression):
        super().__init__()
        if(not isinstance(variable, SVariable)):
            raise SError("SSet: The first argument must be a SVariable")
        if(not isinstance(expression, Expression)):
            raise SError("SSet: The second argument must be an Expression")
        self.variable = variable
        self.expression = expression
    
    def __repr__(self):
        return "(SSet " + str(self.variable) + " " + str(self.expression) + ")"

class SBegin(Expression):
    def __init__(self, expressions):
        super().__init__()
        for var in expressions:
            if(not isinstance(var, Expression)):
                raise SError("SBegin: Not all the arguments are exppressions")
        self.expressions = expressions
    
    def __repr__(self):
        return "(SBegin " + str(self.expressions) + ")"