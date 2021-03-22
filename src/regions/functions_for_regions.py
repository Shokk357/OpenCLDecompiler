from collections import deque
from src.decompiler_data import DecompilerData
from src.regions.region import Region
from src.type_of_node import TypeNode
from src.type_of_reg import Type


def add_parent_and_child(before_r, next_r, region, pred_child, pred_parent):
    for i in range(len(before_r)):
        index = before_r[i].children.index(pred_child[i])
        before_r[i].children[index] = region
        region.add_parent(before_r[i])
    if next_r is not None:
        index = next_r.parent.index(pred_parent)
        next_r.parent[index] = region
        region.add_child(next_r)


def check_if(curr_region):
    return curr_region.type == TypeNode.basic and len(curr_region.children) == 2 \
            and (len(curr_region.children[0].children) > 0
                 and curr_region.children[0].children[0] == curr_region.children[1]
                 or len(curr_region.children[1].children) > 0
                 and curr_region.children[1].children[0] == curr_region.children[0])


def check_if_else(curr_region):
    return curr_region.type == TypeNode.basic and len(curr_region.children) == 2 \
            and len(curr_region.children[0].children) > 0 \
            and len(curr_region.children[1].children) > 0 \
            and curr_region.children[0].children[0] == curr_region.children[1].children[0]


def check_circle(region_start, region_end):
    return len(region_start.children) == 1 and len(region_start.children[0].children) == 1 \
           and region_start.children[0].children[0] == region_end


def create_new_region(prev_reg_1, prev_reg_2, next_reg):
    prev_reg_1.children.remove(next_reg)
    prev_reg_2.children.remove(next_reg)
    position = next_reg.parent.index(prev_reg_1)
    new_fiction_region = Region(TypeNode.linear, next_reg.start)
    next_reg.parent[position] = new_fiction_region
    next_reg.parent.remove(prev_reg_2)
    prev_reg_1.children.append(new_fiction_region)
    prev_reg_2.children.append(new_fiction_region)
    new_fiction_region.parent.append(prev_reg_1)
    new_fiction_region.parent.append(prev_reg_2)
    new_fiction_region.children.append(next_reg)
    return new_fiction_region


def join_regions(before_region, curr_region, next_region, start_region):
    start_now = start_region
    if len(before_region) == 1:
        before_region = before_region[0]
        if before_region.type != TypeNode.basic:
            region = Region(TypeNode.linear, before_region)
            region.end = curr_region
            if before_region == start_now:
                start_now = region
            else:
                parent = before_region.parent[0]
                index = parent.children.index(before_region)
                parent.children[index] = region
                region.add_parent(parent)
            if next_region is not None:
                index = next_region.parent.index(curr_region)
                next_region.parent[index] = region
                region.add_child(next_region)
            if next_region is not None and next_region.type != TypeNode.basic and len(curr_region.parent) == 1:
                region_all = Region(TypeNode.linear, before_region)
                region_all.end = next_region
                if start_now == region:
                    start_now = region_all
                else:
                    parent = before_region.parent[0]
                    index = parent.children.index(region)
                    parent.children[index] = region_all
                    region_all.add_parent(parent)
                if next_region.children:
                    child = next_region.children[0]
                    index = child.parent.index(next_region)
                    child.parent[index] = region_all
                    region_all.add_child(child)
            return start_now

    if next_region is not None and next_region != TypeNode.basic and len(curr_region.parent) == 1:
        region_all = Region(TypeNode.linear, curr_region)
        region_all.end = next_region
        for prev_r in before_region:
            index = prev_r.children.index(curr_region)
            prev_r.children[index] = region_all
            region_all.add_parent(prev_r)
        if next_region.children:
            child = next_region.children[0]
            index = child.parent.index(next_region)
            child.parent[index] = region_all
            region_all.add_child(child)
    return start_region


def make_region_graph_from_cfg():
    decompiler_data = DecompilerData()
    curr_node = decompiler_data.cfg
    region = Region(TypeNode.linear, curr_node)
    decompiler_data.set_starts_regions(curr_node, region)
    decompiler_data.set_ends_regions(curr_node, region)
    visited = [curr_node]
    q = deque()
    q.append(curr_node.children[0])
    while q:
        curr_node = q.popleft()
        if curr_node not in visited:
            visited.append(curr_node)
            if curr_node in decompiler_data.circles or curr_node in decompiler_data.back_edges:
                region_type = TypeNode.backedge
                if curr_node in decompiler_data.circles:
                    region_type = TypeNode.startcircle
                region = Region(region_type, curr_node)
                decompiler_data.set_starts_regions(curr_node, region)
                decompiler_data.set_ends_regions(curr_node, region)
                for c_p in curr_node.parent:
                    if c_p in visited:
                        if decompiler_data.ends_regions.get(c_p) is not None:
                            parent = decompiler_data.ends_regions[c_p]
                        else:
                            parent = decompiler_data.ends_regions[curr_node.parent[0].children[0]]
                        parent.add_child(region)
                        region.add_parent(parent)
            elif len(curr_node.parent) == 1 and (len(curr_node.children) == 1 or len(curr_node.children) == 0):
                if decompiler_data.ends_regions[curr_node.parent[0]].type == TypeNode.linear:
                    region = decompiler_data.ends_regions.pop(curr_node.parent[0])
                    region.end = curr_node
                    decompiler_data.set_ends_regions(curr_node, region)
                else:
                    region = Region(TypeNode.linear, curr_node)
                    decompiler_data.set_starts_regions(curr_node, region)
                    decompiler_data.set_ends_regions(curr_node, region)
                    parent = decompiler_data.ends_regions[curr_node.parent[0]]
                    parent.add_child(region)
                    region.add_parent(parent)
            else:
                region = Region(TypeNode.basic, curr_node)
                decompiler_data.set_starts_regions(curr_node, region)
                decompiler_data.set_ends_regions(curr_node, region)
                flag_of_continue = False
                for c_p in curr_node.parent:
                    if c_p not in visited and curr_node not in decompiler_data.circles:
                        flag_of_continue = True
                        break
                if flag_of_continue:
                    visited.remove(curr_node)
                    continue
                for c_p in curr_node.parent:
                    if c_p in visited:
                        if decompiler_data.ends_regions.get(c_p) is not None:
                            parent = decompiler_data.ends_regions[c_p]
                        else:
                            parent = decompiler_data.ends_regions[curr_node.parent[0].children[0]]
                        parent.add_child(region)
                        region.add_parent(parent)
            for child in curr_node.children:
                if child not in visited:
                    q.append(child)
                else:
                    region.add_child(decompiler_data.starts_regions[child])
                    decompiler_data.set_parent_for_starts_regions(child, region)
                        

def process_if_statement_region(curr_region, visited, start_region, q):
    region = Region(TypeNode.ifstatement, curr_region)
    child0 = curr_region.children[0] if len(curr_region.children[0].parent) == 1 else \
        curr_region.children[1]
    child1 = curr_region.children[1] if len(curr_region.children[1].parent) > 1 else \
        curr_region.children[0]
    before_r = [curr_region.parent[0]]
    prev_child = [curr_region]
    if len(child1.parent) > 2:
        child1 = create_new_region(curr_region, child0, child1)
    region.end = child1
    visited.append(child1)
    visited.append(child0)
    next_r = child1.children[0] if len(child1.children) > 0 else None
    add_parent_and_child(before_r, next_r, region, prev_child, region.end)
    start_region = join_regions(before_r, region, next_r, start_region)
    if region.children:
        for child in region.children:
            if child not in visited:
                q.append(child)
    else:
        q = deque()
        q.append(start_region)
        visited = []
    return visited, q, start_region


def process_if_else_statement_region(curr_region, visited, start_region, q):
    region = Region(TypeNode.ifelsestatement, curr_region)
    child0 = curr_region.children[0]
    child1 = curr_region.children[1]
    region.end = child0.children[0]
    if len(region.end.parent) > 2:
        region.end = create_new_region(child0, child1, child0.children[0])
    prev_child = [curr_region]
    visited.append(child1)
    visited.append(child0)
    visited.append(region.end)
    before_r = [curr_region.parent[0]]
    next_r = region.end.children[0]
    add_parent_and_child(before_r, next_r, region, prev_child, region.end)
    start_region = join_regions(before_r, region, next_r, start_region)
    if region.children:
        for child in region.children:
            if child not in visited:
                q.append(child)
    else:
        q = deque()
        q.append(start_region)
        visited = []
    return visited, q, start_region


def process_circle(region_start, region_end):
    decompiler_data = DecompilerData()
    region = Region(TypeNode.circle, region_start)
    region.end = region_end
    prev_child = [region_start]
    before_r = [region_start.parent[0]]
    next_r = region.end.children[1]
    add_parent_and_child(before_r, next_r, region, prev_child, region.end)
    used_versions_of_registers = set()
    curr_node = region_start.start
    while curr_node != region_end.start:
        list_of_reg_nums = list(range(1, len(curr_node.instruction))[1:])
        list_of_reg_nums = list_of_reg_nums if len(curr_node.instruction) == 1 else list_of_reg_nums + [1]
        for num_of_register in list_of_reg_nums:
            register = curr_node.instruction[num_of_register]
            if len(register) > 1 and register[1] == "[":
                register = register[0] + register[2: register.find(":")]
            if ("cmp" in curr_node.instruction[0] or num_of_register > 1) and curr_node.state.registers.get(register):
                if register == curr_node.instruction[1] and "cmp" not in curr_node.instruction[0]:
                    used_versions_of_registers.add(curr_node.parent[0].state.registers[register].version)
                else:
                    used_versions_of_registers.add(curr_node.state.registers[register].version)
            if "cmp" not in curr_node.instruction[0] and num_of_register == 1 and curr_node.state.registers.get(register):
                first_reg_version = curr_node.state.registers[register].version
                separation = first_reg_version.find("_")
                first_reg_prev_version = first_reg_version[:separation + 1] + str(int(first_reg_version[separation+1:]) - 1)
                if first_reg_prev_version in used_versions_of_registers:
                    if decompiler_data.circles_variables.get(first_reg_prev_version):
                        variable = decompiler_data.circles_variables[first_reg_prev_version]
                    else:
                        variable = "var" + str(decompiler_data.num_of_var)
                        decompiler_data.num_of_var += 1
                    if curr_node.state.registers[register].type == Type.param_global_id_x:
                        variable = "*" + variable
                    # decompiler_data.make_var(first_reg_prev_version, variable,
                    #                          curr_node.state.registers[register].type_of_data)
                    decompiler_data.checked_variables[first_reg_prev_version] = variable
                    # decompiler_data.checked_variables[first_reg_version] = variable
                    decompiler_data.circles_variables[first_reg_version] = variable
                    decompiler_data.circles_nodes_for_variables[curr_node] = first_reg_version
                    # decompiler_data.variables[first_reg_version] = variable
                    decompiler_data.names_of_vars[variable] = curr_node.state.registers[register].type_of_data
                    decompiler_data.variables[first_reg_prev_version] = variable
        curr_node = curr_node.children[0]


def process_control_structures_in_circle(region_start, region_end):
    start_region = region_start
    visited = []
    q = deque()
    q.append(start_region)
    after_region_end = region_end.children[0]
    while start_region.children[0] != after_region_end:
        curr_region = q.popleft()
        if curr_region not in visited:
            visited.append(curr_region)
            if check_circle(region_start, region_end):
                process_circle(region_start, region_end)
                return
            elif curr_region.type == TypeNode.basic and len(curr_region.children) == 2 \
                    and (curr_region.children[0] == after_region_end or curr_region.children[1] == after_region_end):
                curr_region.type = TypeNode.breakregion  # надо отдельно написать на return и обрезание на break
                if curr_region.children:
                    for child in curr_region.children:
                        if child not in visited:
                            q.append(child)
                else:
                    q = deque()
                    q.append(start_region)
                    visited = []
            else:
                preprocess_if_and_if_else(curr_region, visited, start_region, q)


def get_one_circle_region(q_circles, curr_region, start_region, region_start, region_end):
    while q_circles:
        circle_region = q_circles.pop()
        if circle_region.type == TypeNode.backedge:
            circle_region.type = TypeNode.continueregion
            join_regions([circle_region.parent[0]], circle_region,
                         circle_region.children[0], start_region)  # not good enough
        elif curr_region.start.instruction[1] == circle_region.start.instruction[0][:-1]:
            region_start = circle_region
            curr_circle = None
        else:
            start_region = circle_region
            curr_circle = circle_region
            q_circles.append(circle_region)
            break
    if check_circle(region_start, region_end):
        process_circle(region_start, region_end)
    else:
        process_control_structures_in_circle(region_start, region_end)
    return curr_circle, start_region, q_circles, region_start


def find_circles():
    decompiler_data = DecompilerData()
    start_region = decompiler_data.starts_regions[decompiler_data.circles[0]]
    q_circles = deque()  # очередь из элементов цикла
    curr_circle = start_region  # текущий старт цикла
    q_circles.append(start_region)
    q_regions = deque()  # очередь из всех регионов
    q_regions.append(start_region.children[0])
    visited = [start_region]
    while q_regions:
        curr_region = q_regions.popleft()
        if curr_region not in visited:
            visited.append(curr_region)
            if curr_region.type == TypeNode.backedge:
                if curr_region.start.instruction[1] == curr_circle.start.instruction[0][:-1]:
                    q_circles.append(curr_region)
                else:
                    region_end = curr_region
                    region_start = curr_circle
                    curr_circle, start_region, q_circles, region_start =\
                        get_one_circle_region(q_circles, curr_region, start_region, region_start, region_end)
            elif curr_region.type == TypeNode.startcircle:
                curr_circle = curr_region
                q_circles.append(curr_region)
            for curr_child in curr_region.children:
                if curr_child not in visited:
                    q_regions.append(curr_child)
    if q_circles:
        region_end = q_circles.pop()
        curr_region = region_end
        region_start = None
        get_one_circle_region(q_circles, curr_region, start_region, region_start, region_end)


def preprocess_if_and_if_else(curr_region, visited, start_region, q):
    if curr_region.type != TypeNode.linear:
        if check_if(curr_region):
            visited, q, start_region = process_if_statement_region(curr_region, visited, start_region, q)
        elif check_if_else(curr_region):
            visited, q, start_region = process_if_else_statement_region(curr_region, visited, start_region, q)
        else:
            if curr_region.children:
                for child in curr_region.children:
                    if child not in visited:
                        q.append(child)
            else:
                q = deque()
                q.append(start_region)
                visited = []
    else:
        if curr_region.children:
            for child in curr_region.children:
                if child not in visited:
                    q.append(child)
        else:
            q = deque()
            q.append(start_region)
            visited = []
    return visited, q, start_region


def process_region_graph():
    decompiler_data = DecompilerData()
    start_region = decompiler_data.starts_regions[decompiler_data.cfg]
    if decompiler_data.circles:
        find_circles()
    visited = []
    q = deque()
    q.append(start_region)
    while start_region.children:
        curr_region = q.popleft()
        if curr_region not in visited:
            visited.append(curr_region)
            if curr_region.type == TypeNode.circle:
                start_region = join_regions([curr_region.parent[0]], curr_region, curr_region.children[0], start_region)
                if curr_region.children:
                    for child in curr_region.children:
                        if child not in visited:
                            q.append(child)
                else:
                    q = deque()
                    q.append(start_region)
                    visited = []
            else:
                visited, q, start_region = preprocess_if_and_if_else(curr_region, visited, start_region, q)
    decompiler_data.improve_cfg = start_region
