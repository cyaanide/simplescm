from compilerenums import *
import struct

class AssemblerError(SyntaxError):
    pass

class Assembler():

    def __init__(self, constants, instructions, procedures):
        self.constants = constants
        self.instructions = instructions
        self.procedure = procedures
        self.output = bytearray()
        
    def enum_to_byte(self, oppcode):
        return oppcode.value.to_bytes(1)

    def uid_to_4_bytes(self, uid):
        return uid.to_bytes(4)

    def float_to_8_bytes(self, num):
        return bytearray(struct.pack("<d", num))

    def assemble_constant(self, constant):
        output = bytearray()
        uid = constant[0]
        typ = constant[1][0]
        values = constant[1][1]
        if(typ ==  Types.number):
            output += self.uid_to_4_bytes(uid)
            output += self.enum_to_byte(Types.number)
            output += self.float_to_8_bytes(values[0])
            return output
        elif(typ == Types.string):
            pass
        elif(typ == Types.symbol):
            pass
        elif(typ == Types.list):
            pass
        else:
            raise str(type(typ)) + " can't be processed in assemble_constant"
    
    def assemble_constants(self):
        self.output += self.enum_to_byte(OppCodes.data_start)
        for const in self.constants:
            self.output += self.assemble_constant(const)
        self.output += self.enum_to_byte(OppCodes.data_end)
        print(self.output)