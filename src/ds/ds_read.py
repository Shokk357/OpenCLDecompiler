from base_instruction import BaseInstruction
from decompiler_data import DecompilerData
from integrity import Integrity
from register import Register


class DsRead(BaseInstruction):
    def execute(self, node, instruction, flag_of_status, suffix):
        decompiler_data = DecompilerData.Instance()
        output_string = ""
        if suffix == "b32":
            vdst = instruction[1]
            addr = instruction[2]
            offset = int(instruction[3][7:]) if len(instruction) == 4 else 0
            new_value, src0_flaf, src1_flag = decompiler_data.make_op(node, addr, "4", " / ")
            name = decompiler_data.lds_vars[offset][0] + "[" + new_value + "]"
            if flag_of_status:
                node.state.registers[vdst] = Register(name, node.state.registers[name].type, Integrity.integer)
                node.state.make_version(decompiler_data.versions, vdst)
                node.state.registers[vdst].type_of_data = "u" + suffix[1:]
                return node
            return output_string

        elif suffix == "b64":
            vdst = instruction[1]
            addr = instruction[2]
            offset = int(instruction[3][7:]) if len(instruction) == 4 else 0
            name = self.lds_vars[offset][0] + "[" + node.state.registers[addr].var + "]"
            if flag_of_status:
                node.state.registers[vdst] = Register(name, node.state.registers[name].type, Integrity.integer)
                node.state.make_version(self.versions, vdst)
                node.state.registers[vdst].type_of_data = "u" + suffix[1:]
                return node
            return output_string