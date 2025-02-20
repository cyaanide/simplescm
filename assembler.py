from compilerenums import *
import struct

class AssemblerError(SyntaxError):
    pass

class Assembler():

    def __init__(self, constants, instructions, procedures):
        self.constants = constants
        self.instructions = instructions
        self.procedure = procedures
        self.output = []
        
    def enum_to_byte(self, oppcode):
        return bytearray(oppcode.value.to_bytes(1))
    
    def num_to_byte(self, num):
        return bytearray(num.to_bytes(1))

    def uid_to_4_bytes(self, uid):
        return bytearray(uid.to_bytes(4))

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
            output += self.uid_to_4_bytes(uid)
            output += self.enum_to_byte(Types.string)
            output += self.string_to_byes(values[0])
            return output
        elif(typ == Types.symbol):
            output += self.uid_to_4_bytes(uid)
            output += self.enum_to_byte(Types.symbol)
            output += self.string_to_byes(values[0])
            return output
        elif(typ == Types.list):
            output += self.uid_to_4_bytes(uid)
            output += self.enum_to_byte(Types.list)
            output += self.uid_to_4_bytes(len(values))
            for val in values:
                output += self.uid_to_4_bytes(val)
            return output
        else:
            raise str(type(typ)) + " can't be processed in assemble_constant"
    
    def assemble_constants(self):
        self.output.append(self.enum_to_byte(OppCodes.data_start))
        for const in self.constants:
            self.output.append(self.assemble_constant(const))
        self.output.append(self.enum_to_byte(OppCodes.data_end))
        
    def no_of_bytes(self, lst):
        return sum(map(len, lst))
    
    # Return a null terminated string in bytearray
    def string_to_byes(self, str):
        return bytearray(str, "ascii") + bytearray(1)
        
    # return:
    # a. A list of compiled bytecode
    # b. A dictionary where uid is the key and the value is the list of array indicies where I need to put in my label location 
    # c. A dictionary where the uid is the key and the value is the index of the next instruction after the label instruction 
    def assemble_body(self, instruction_body):
        output = []
        to_replace = {}
        label_locations = {}
        lambda_location = {}
        for instruction in instruction_body:
            opp_code = instruction[0]
            operand = instruction[1]
            if(opp_code == OppCodes.opp_null):
                output.append(self.enum_to_byte(OppCodes.opp_null))
            elif(opp_code == OppCodes.lookup):
                compiled = self.enum_to_byte(OppCodes.lookup)
                if(type(operand) != str):
                    raise AssemblerError(str(type(operand)) + " not of type string")
                # Null terminated string
                compiled += self.string_to_byes(operand)
                output.append(compiled)
            elif(opp_code == OppCodes.load_const):
                output.append(self.enum_to_byte(OppCodes.load_const) + self.uid_to_4_bytes(operand))
            elif(opp_code == OppCodes.bind):
                no_vars = len(operand)
                compiled = self.enum_to_byte(OppCodes.bind)
                compiled += self.num_to_byte(no_vars)
                for i in range(no_vars):
                    compiled += self.string_to_byes(operand[i])
                output.append(compiled)
            elif(opp_code == OppCodes.apply):
                output.append(self.enum_to_byte(OppCodes.apply))
            elif(opp_code == OppCodes.ret):
                output.append(self.enum_to_byte(OppCodes.ret))
            elif(opp_code == OppCodes.save_continuation):
                compiled = self.enum_to_byte(OppCodes.save_continuation) 
                len_so_far = len(output)
                l = to_replace.get(operand)
                if(l):
                    l.append(len_so_far)
                else:
                    to_replace[operand] = [len_so_far,]
                # Add zeroed data, that will be replaced with the actuall value later
                compiled += self.uid_to_4_bytes(0)
                output.append(compiled)
            elif(opp_code == OppCodes.if_false_branch):
                compiled = self.enum_to_byte(OppCodes.if_false_branch) 
                len_so_far = len(output) 
                l = to_replace.get(operand)
                if(l):
                    l.append(len_so_far)
                else:
                    to_replace[operand] = [len_so_far,]
                # Add zeroed data, that will be replaced with the actuall value later
                compiled += self.uid_to_4_bytes(0)
                output.append(compiled)
            elif(opp_code == OppCodes.if_true_branch):
                compiled = self.enum_to_byte(OppCodes.if_true_branch) 
                len_so_far = len(output) 
                l = to_replace.get(operand)
                if(l):
                    l.append(len_so_far)
                else:
                    to_replace[operand] = [len_so_far,]
                # Add zeroed data, that will be replaced with the actuall value later
                compiled += self.uid_to_4_bytes(0)
                output.append(compiled)
            elif(opp_code == OppCodes.branch):
                compiled = self.enum_to_byte(OppCodes.branch) 
                len_so_far = len(output) 
                l = to_replace.get(operand)
                if(l):
                    l.append(len_so_far)
                else:
                    to_replace[operand] = [len_so_far,]
                # Add zeroed data, that will be replaced with the actuall value later
                compiled += self.uid_to_4_bytes(0)
                output.append(compiled)
            elif(opp_code == OppCodes.push):
                output.append(self.enum_to_byte(OppCodes.push))
            elif(opp_code == OppCodes.make_closure):
                len_so_far = len(output)
                l = lambda_location.get(operand)
                if(l):
                    l.append(len_so_far)
                else:
                    lambda_location[operand] = [len_so_far,]
                # Add zeroed 4 bytes that will be replaced later
                output.append(self.enum_to_byte(OppCodes.make_closure) + self.uid_to_4_bytes(0))
            elif(opp_code == OppCodes.set):
                output.append(self.enum_to_byte(OppCodes.set) + self.string_to_byes(operand))
            elif(opp_code == OppCodes.define):
                output.append(self.enum_to_byte(OppCodes.define) + self.string_to_byes(operand))
            elif(opp_code == OppCodes.ext):
                output.append(self.enum_to_byte(OppCodes.ext))
            elif(opp_code == OppCodes.label):
                # Technically we have no need to add a null op, but do it to make it easier to debug
                output.append(self.enum_to_byte(OppCodes.label))
                len_so_far = len(output) 
                if(label_locations.get(operand)):
                    raise AssemblerError(str(operand) + " already in label_locations")
                label_locations[operand] = len_so_far
            elif(opp_code == OppCodes.proc_end):
                output.append(self.enum_to_byte(OppCodes.proc_end))
            elif(opp_code == OppCodes.data_start):
                raise AssemblerError("Should not have a data_start in the body")
            elif(opp_code == OppCodes.data_end):
                raise AssemblerError("Should not have a data_end in the body")
            else:
                raise AssemblerError(str(type(instruction)) + " is not one of the enums in OppCodes")
        return (output, to_replace, label_locations, lambda_location)