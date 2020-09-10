from base_instruction import BaseInstruction
from decompiler_data import DecompilerData


class SSwappc(BaseInstruction):
    def execute(self, node, instruction, flag_of_status, suffix, output_string):
        decompiler_data = DecompilerData.Instance()
        if suffix == 'b64':
            sdst = instruction[1]
            ssrc0 = instruction[2]
            decompiler_data.output_file.write(sdst + " = pc + 4\n")
            decompiler_data.output_file.write("pc = " + ssrc0 + "\n")
