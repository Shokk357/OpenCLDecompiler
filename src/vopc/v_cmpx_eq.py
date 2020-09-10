from base_instruction import BaseInstruction
from decompiler_data import DecompilerData


class VCmpxEq(BaseInstruction):
    def execute(self, node, instruction, flag_of_status, suffix, output_string):
        decompiler_data = DecompilerData.Instance()
        if suffix == "f64":
            sdst = instruction[1]
            src0 = instruction[2]
            src1 = instruction[3]
            decompiler_data.output_file.write(sdst + " = as_double(" + src0 + ") == as_double(" + src1 + ")\n")
            decompiler_data.output_file.write("exec = " + sdst + "\n")
