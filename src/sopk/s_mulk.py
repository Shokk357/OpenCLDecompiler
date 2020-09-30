from src.base_instruction import BaseInstruction
from src.decompiler_data import DecompilerData
from src.integrity import Integrity
from src.register import Register
from src.type_of_reg import Type


class SMulk(BaseInstruction):
    def execute(self, node, instruction, flag_of_status, suffix):
        decompiler_data = DecompilerData.Instance()
        output_string = ""
        if suffix == 'i32':
            sdst = instruction[1]
            simm16 = instruction[2][instruction[2].find("x") + 1:]
            if flag_of_status:
                new_val, sdst_flag, simm16_flag = decompiler_data.make_op(node, sdst, simm16, " * ")
                node.state.registers[sdst] = Register(new_val, Type.unknown, Integrity.integer)
                node.state.make_version(decompiler_data.versions, sdst)
                node.state.registers[sdst].make_prev()
                node.state.registers[sdst].type_of_data = suffix
                return node
            return output_string
