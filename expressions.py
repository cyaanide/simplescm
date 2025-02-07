
class SError(Exception):
    pass

class Expression:
    pass

class SNumber(Expression):
    def __init__(self, num):
        if(type(num) != float):
            raise SError("SNumber: not a float")
        self.value = num

    def __repr__(self):
        return str(self.value)

class SString(Expression):
    def __init__(self, string):
        if(type(string) != str):
            raise SError("SString: not a string")
        self.value = string
    
    def __repr__(self):
        return str(self.value)
    


class SBool(Expression):
    def __init__(self, boolean):
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
        if(type(string) != str):
            raise SError("SVariable: not a string")
        self.value = string
    
    def __repr__(self):
        return str(self.value)


class SIf(Expression):
    def __init__(self, test, consequent, alternative):
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
        
            
