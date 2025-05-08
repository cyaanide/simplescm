from astgenerator import ASTGenerator
from compiler import Compiler
from expressions import *
from compilerenums import *


class CompilerTester:
    def __init__(self):
        pass

    def astgenerator_test(self):
        testcases = {
            '(quote (x y ()))' : [SConstList([SSymbol("x"), SSymbol("y"), SEmptyList()])],
            '(define x 123)' : [SDefine(SVariable("x"), SNumber(123.0))],
            '(set! x 123)' : [SSet(SVariable("x"), SNumber(123.0))],
            '(let ((x 123)) x)' : [SLet([(SVariable('x'), SNumber(123.0))], [SVariable('x')])],
            '(if x y z)' : [SIf(SVariable('x'), SVariable('y'), SVariable('z'))],
            '(+ 1 2)' : [SProcApplication(SVariable('+'), [SNumber(1.0), SNumber(2.0)])],
            '(lambda (x) x)' : [SLambda([SVariable('x')], [SVariable('x')])],
            '(and 1 2)' : [SAnd([SNumber(1.0), SNumber(2.0)])],
            '(or 1 2)' : [SOr([SNumber(1.0), SNumber(2.0)])],
            '123' : [SNumber(123.0),],
            '"khilan"' : [SString("khilan"),],
            '(quote x)' : [SSymbol("x"),],
            '#f' : [SBool("#f")],
            'x' : [SVariable("x")],
        }
        
        for code in testcases:
            astgen = ASTGenerator(code)
            expected = testcases[code]
            got = astgen.generate_ast()
            if(got != expected):
                raise AssertionError(f"\nfor code:\n{code}\n-------\ngot:\n{got}\n-------\nexpected:\n{expected}")
            
if __name__ == "__main__":
    tester = CompilerTester()
    print("Testing ASTGenerator")
    tester.astgenerator_test()
    print("Testing Compiler")
    tester.compilertest()