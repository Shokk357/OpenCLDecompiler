import copy
from collections import deque
from src.type_of_reg import Type
from src.decompiler_data import DecompilerData


def update_reg_version(reg, curr_node, max_version, version_of_reg):
    decompiler_data = DecompilerData.Instance()
    if len(version_of_reg) == 1:
        if curr_node.state.registers.get(reg) is None or curr_node.state.registers[reg] is None:
            for p in curr_node.parent:
                if p.state.registers[reg] is not None:
                    curr_node.state.registers[reg] = p.state.registers[reg]
                    break
    elif len(version_of_reg) > 1:
        curr_node.state.registers[reg].version = reg + "_" + str(max_version + 1)
        curr_node.state.registers[reg].prev_version = list(version_of_reg)
        variable = "var" + str(decompiler_data.num_of_var)
        if curr_node.state.registers[reg].type == Type.param_global_id_x:
            variable = "*" + variable
        curr_node.state.registers[reg].val = variable
        decompiler_data.num_of_var += 1
        for ver in version_of_reg:
            decompiler_data.variables[ver] = variable
        decompiler_data.checked_variables[curr_node.state.registers[reg].version] = variable
        decompiler_data.versions[reg] = max_version + 1
    return curr_node


def check_for_many_versions():
    decompiler_data = DecompilerData.Instance()
    curr_node = decompiler_data.cfg
    visited = [curr_node]
    q = deque()
    q.append(curr_node.children[0])
    while q:
        curr_node = q.popleft()
        if curr_node not in visited:
            visited.append(curr_node)
            if len(curr_node.parent) < 2:
                if decompiler_data.checked_variables != {}:
                    instruction = curr_node.instruction
                    if instruction[0].find("mul_lo") != -1:
                        print(instruction)
                    if instruction != "branch" and len(instruction) > 1:
                        for num_of_reg in list(range(1, len(curr_node.instruction))):
                            register = curr_node.instruction[num_of_reg]
                            if (curr_node.instruction[0].find("flat_store") != -1 or num_of_reg > 1) and len(register) > 1 \
                                    and curr_node.instruction[0].find("cnd") == -1:
                                if register[1] == "[":
                                    register = register[0] + register[2: register.find(":")]
                                first_reg = curr_node.instruction[1]
                                if first_reg[1] == "[":
                                    first_reg = first_reg[0] + first_reg[2: first_reg.find(":")]
                                if curr_node.state.registers.get(register) is not None:
                                    checked_version = curr_node.state.registers[register].version
                                else:
                                    continue
                                if first_reg == register:
                                    checked_version = curr_node.parent[0].state.registers[register].version
                                if curr_node.state.registers.get(register) is not None \
                                        and decompiler_data.checked_variables.get(checked_version) is not None \
                                        and curr_node.state.registers[register].type_of_data is not None \
                                        and (register != "vcc" or instruction[0].find("and_saveexec") != -1):
                                    var_name = decompiler_data.checked_variables[checked_version]
                                    if decompiler_data.names_of_vars.get(var_name) is None:
                                        if decompiler_data.checked_variables.get(curr_node.parent[0].state.registers[register].version) is not None:
                                            decompiler_data.names_of_vars[var_name] = \
                                                curr_node.parent[0].state.registers[register].type_of_data
                                        else:
                                            decompiler_data.names_of_vars[var_name] = \
                                                curr_node.state.registers[register].type_of_data
            else:
                flag_of_continue = False
                for c_p in curr_node.parent:
                    if c_p not in visited:
                        flag_of_continue = True
                        break
                if flag_of_continue:
                    visited.remove(curr_node)
                    continue
            for child in curr_node.children:
                if child not in visited:
                    q.append(child)


def remove_unusable_versions():
    decompiler_data = DecompilerData.Instance()
    keys = []
    for key in decompiler_data.variables.keys():
        if decompiler_data.variables[key] not in decompiler_data.names_of_vars.keys():
            keys.append(key)
    for key in keys:
        decompiler_data.variables.pop(key)


def update_value_for_reg(first_reg, curr_node):
    for child in curr_node.children:
        if len(child.parent) < 2 and curr_node.state.registers[first_reg].version == child.state.registers[first_reg].version:
            child.state.registers[first_reg] = copy.deepcopy(curr_node.state.registers[first_reg])
            update_value_for_reg(first_reg, child)


def change_values():
    decompiler_data = DecompilerData.Instance()
    changes = {}
    curr_node = decompiler_data.cfg
    visited = [curr_node]
    q = deque()
    q.append(curr_node.children[0])
    while q:
        curr_node = q.popleft()
        if curr_node not in visited:
            visited.append(curr_node)
            if len(curr_node.parent) < 2:
                instruction = curr_node.instruction
                if instruction != "branch" and len(instruction) > 1:
                    for num_of_reg in list(range(1, len(curr_node.instruction))):
                        register = curr_node.instruction[num_of_reg]
                        if (curr_node.instruction[0].find("flat_store") != -1 or num_of_reg > 1) and len(register) > 1 \
                                and curr_node.instruction[0].find("cnd") == -1:
                            if register[1] == "[":
                                register = register[0] + register[2: register.find(":")]
                            first_reg = curr_node.instruction[1]
                            if first_reg[1] == "[":
                                first_reg = first_reg[0] + first_reg[2: first_reg.find(":")]
                            if curr_node.state.registers.get(register) is not None:
                                check_version = curr_node.state.registers[register].version
                            else:
                                continue
                            if register == first_reg:
                                if curr_node.parent[0].state.registers.get(register) is not None:
                                    check_version = curr_node.parent[0].state.registers[register].version
                                else:
                                    continue
                            if curr_node.state.registers.get(register) is not None \
                                    and changes.get(check_version) \
                                    and curr_node.state.registers[register].type_of_data is not None \
                                    and (register != "vcc" or instruction[0].find("and_saveexec") != -1):
                                if instruction[0].find("flat_store") != -1:
                                    if num_of_reg == 1:
                                        node_registers = curr_node.parent[0].state.registers
                                    else:
                                        node_registers = curr_node.state.registers
                                        first_reg = register
                                elif instruction[0].find("and_saveexec") != -1:
                                    node_registers = curr_node.state.registers
                                    first_reg = "exec"
                                else:
                                    node_registers = curr_node.state.registers
                                copy_val_prev = copy.deepcopy(node_registers[first_reg].val)
                                node_registers[first_reg].val = node_registers[first_reg].val.replace(
                                    changes[check_version][1],
                                    changes[check_version][0])
                                copy_val_last = copy.deepcopy(node_registers[first_reg].val)
                                if copy_val_prev != copy_val_last:
                                    changes[node_registers[first_reg].version] = [copy_val_last, copy_val_prev]
                                    update_value_for_reg(first_reg, curr_node)
                            if curr_node.state.registers.get(register) is not None \
                                    and decompiler_data.variables.get(check_version) is not None \
                                    and curr_node.state.registers[register].type_of_data is not None \
                                    and (register != "vcc" or instruction[0].find("and_saveexec") != -1):
                                val_reg = curr_node.state.registers[register].val
                                if register == first_reg:
                                    val_reg = curr_node.parent[0].state.registers[first_reg].val
                                copy_val_prev = copy.deepcopy(curr_node.state.registers[first_reg].val)
                                if decompiler_data.checked_variables.get(check_version) is not None:
                                    curr_node.state.registers[first_reg].val = \
                                        curr_node.state.registers[first_reg].val.replace(val_reg, decompiler_data.checked_variables[check_version])
                                else:
                                    curr_node.state.registers[first_reg].val = \
                                        curr_node.state.registers[first_reg].val.replace(val_reg, decompiler_data.variables[check_version])
                                copy_val_last = copy.deepcopy(curr_node.state.registers[first_reg].val)
                                if copy_val_prev != copy_val_last:
                                    changes[curr_node.state.registers[first_reg].version] = [copy_val_last, copy_val_prev]
                                    update_value_for_reg(first_reg, curr_node)
            else:
                flag_of_continue = False
                for c_p in curr_node.parent:
                    if c_p not in visited:
                        flag_of_continue = True
                        break
                if flag_of_continue:
                    visited.remove(curr_node)
                    continue
            for child in curr_node.children:
                if child not in visited:
                    q.append(child)