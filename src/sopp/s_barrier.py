from src.base_instruction import BaseInstruction


class SBarrier(BaseInstruction):
    def execute(self, node, instruction, flag_of_status, suffix):
        if flag_of_status:
            return node
        output_string = "barrier(CLK_LOCAL_MEM_FENCE)"
        return output_string
