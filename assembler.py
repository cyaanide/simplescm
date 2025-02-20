from compilerenums import *
import struct

class AssemblerError(SyntaxError):
    pass

class Assembler():

    def __init__(self, constants, main, procedures):
        self.constants = constants
        self.main = main
        self.procedures = procedures
        self.assembled = []
        
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
        output = []
        output.append(self.enum_to_byte(OppCodes.data_start))
        for const in self.constants:
            output.append(self.assemble_constant(const))
        output.append(self.enum_to_byte(OppCodes.data_end))
        return output
        
    def no_of_bytes_in_a_body(self, lst):
        return sum(map(len, lst))
    def no_of_bytes_in_list_body(self, lst_bodies):
        return sum(map(self.no_of_bytes_in_a_body, lst_bodies))
    
    # Return a null terminated string in bytearray
    def string_to_byes(self, str):
        return bytearray(str, "ascii") + bytearray(1)
        
    def assemble_body(self, instruction_body):
        output = []
        # {label_uid: [line_that_needs_this_label,]}
        lines_that_need_label = {}
        # {label_uid: label_line}
        label_locations = {}
        # {lambda_uid: line_that_needs_the_ip_of_this_lambda}
        lines_that_need_lambda = {}
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
                l = lines_that_need_label.get(operand)
                if(l):
                    l.append(len_so_far)
                else:
                    lines_that_need_label[operand] = [len_so_far,]
                # Add zeroed data, that will be replaced with the actuall value later
                compiled += self.uid_to_4_bytes(0)
                output.append(compiled)
            elif(opp_code == OppCodes.if_false_branch):
                compiled = self.enum_to_byte(OppCodes.if_false_branch) 
                len_so_far = len(output) 
                l = lines_that_need_label.get(operand)
                if(l):
                    l.append(len_so_far)
                else:
                    lines_that_need_label[operand] = [len_so_far,]
                # Add zeroed data, that will be replaced with the actuall value later
                compiled += self.uid_to_4_bytes(0)
                output.append(compiled)
            elif(opp_code == OppCodes.if_true_branch):
                compiled = self.enum_to_byte(OppCodes.if_true_branch) 
                len_so_far = len(output) 
                l = lines_that_need_label.get(operand)
                if(l):
                    l.append(len_so_far)
                else:
                    lines_that_need_label[operand] = [len_so_far,]
                # Add zeroed data, that will be replaced with the actuall value later
                compiled += self.uid_to_4_bytes(0)
                output.append(compiled)
            elif(opp_code == OppCodes.branch):
                compiled = self.enum_to_byte(OppCodes.branch) 
                len_so_far = len(output) 
                l = lines_that_need_label.get(operand)
                if(l):
                    l.append(len_so_far)
                else:
                    lines_that_need_label[operand] = [len_so_far,]
                # Add zeroed data, that will be replaced with the actuall value later
                compiled += self.uid_to_4_bytes(0)
                output.append(compiled)
            elif(opp_code == OppCodes.push):
                output.append(self.enum_to_byte(OppCodes.push))
            elif(opp_code == OppCodes.make_closure):
                len_so_far = len(output)
                l = lines_that_need_lambda.get(operand)
                if(l):
                    raise AssemblerError("make_closure uid not unique")
                else:
                    lines_that_need_lambda[operand] = len_so_far
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
        return (output, lines_that_need_label, label_locations, lines_that_need_lambda)
    
    
    def debug_output(self):
        output = ""
        cur = 0
        for body in self.assembled:
            for ins in body:
                output += hex(cur).ljust(6) + "| "
                output += ", ".join(hex(b) for b in ins) + "\n"
                cur += len(ins)
            output += "------------\n"
        return output
    
    def sub_in_labels(self, assembled_body, label_replacement, label_location, offset):
        for label_uid in label_location:
            label_line = label_location[label_uid]
            ip = offset + (self.no_of_bytes_in_a_body(assembled_body[:label_line]))
            lines_to_replace = label_replacement[label_uid]
            for line in lines_to_replace:
                assembled_body[line][1:5] = self.uid_to_4_bytes(ip)

    def assemble(self):
        bodies = []
        # {procedure_uid: index_in_body}
        index_of_procedure = {}
        # {procedure_uid: (body_index, line_index)}
        lines_that_need_procedure = {}
        
        assembled_consts = self.assemble_constants()
        bodies.append(assembled_consts)
        
        (main_assembled, lines_in_main_that_need_label, label_locations, lines_in_main_that_need_lambda) = self.assemble_body(self.main)
        bytes_so_far = self.no_of_bytes_in_list_body(bodies)
        self.sub_in_labels(main_assembled, lines_in_main_that_need_label, label_locations, bytes_so_far)
        for lambda_id in lines_in_main_that_need_lambda:
            if(lines_that_need_procedure.get(lambda_id)):
                raise AssemblerError("Trying to add an already existing uid to lines_that_need_procedure")
            lines_that_need_procedure[lambda_id] = (len(bodies), lines_in_main_that_need_lambda[lambda_id])
        bodies.append(main_assembled)
        
        for proc in self.procedures:
            uid = proc[0]
            proc_body = proc[1]
            index_of_procedure[uid] = len(bodies)
            (assembled_body, lines_that_need_label, label_locations, lines_that_need_lambda) = self.assemble_body(proc_body)
            bytes_so_far = self.no_of_bytes_in_list_body(bodies)
            self.sub_in_labels(assembled_body, lines_that_need_label, label_locations, bytes_so_far)
            for lambda_id in lines_that_need_lambda:
                if(lines_that_need_procedure.get(lambda_id)):
                    raise AssemblerError("Trying to add an already existing uid to lines_that_need_procedure")
                lines_that_need_procedure[lambda_id] = (len(bodies), lines_that_need_lambda[lambda_id])
            bodies.append(assembled_body)

        for lambda_id in lines_that_need_procedure:
            (body_index, line_in_body) = lines_that_need_procedure[lambda_id]
            lambda_pos_in_bodies = index_of_procedure[lambda_id]
            lambda_pos = self.no_of_bytes_in_list_body(bodies[:lambda_pos_in_bodies])
            bodies[body_index][line_in_body][1:5] = self.uid_to_4_bytes(lambda_pos)

        self.assembled = bodies
        final_and = bytearray()
        for body in bodies:
            for line in body:
                final_and += line
        return final_and
