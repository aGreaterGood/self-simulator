from turingmachine import TuringMachine


class SelfSimTM(TuringMachine):
    BLANK = 0
    
    def __init__(self, tape, start, end):
        super().__init__(tape, self.self_sim_transition, start, end, BLANK)
        self.level_step_count = []
        self.state_set = set()
        self.info_set = set()
        self.tagged_state_count = dict()
        self.reg_set = set()
    
    def is_aligned(self, level):
        if level == 0:
            return True
        elif level == 1:
            if self.state == ('read_state', None):
                return True
            return False
        elif self.is_aligned(level - 1):
            scale = 4 ** (level - 1)
            inds = [(self.head_pos // scale) * scale + (scale // 4) * x + (scale // 4) - 1 for x in range(3)]
            semistate = tuple(self.tape[i] for i in inds if i<len(self.tape))
            if semistate == (('read_state', None), 0, 0):
                return True
        return False

    def recursive_print(self, level=0):
        scale = 4 ** level
        while scale <= len(self.tape):
            res = []
            for i in range(len(self.tape) // scale):
                if self.head_pos // scale == i:
                    res.append(('<!>', self.tape[(i + 1) * scale - 1]))
                else:
                    res.append(self.tape[(i + 1) * scale - 1])
            if scale == 1:
                print('>>Scale', scale, '  --  ', self.head_pos, '  --  ', self.state)
                print(res)
            else:
                inds = [(self.head_pos // scale) * scale + (scale // 4) * x + (scale // 4) - 1 for x in range(3)]
                semistate = tuple(self.tape[i] for i in inds if i<len(self.tape))
                print('Scale', scale, '  --  ', self.head_pos // scale, '  --  ', semistate)
                print(res)
            scale *= 4

    def run(self):
        def pow10(num):
            if num == 1:
                return True
            if num % 10 == 0 and pow10(num // 10):
                return True

        while(self.state != self.end):
            self.info_set.add(self.tape[self.head_pos])
            if self.state[:2] in self.tagged_state_count:
                self.tagged_state_count[self.state[:2]] += 1
            else:
                self.tagged_state_count[self.state[:2]] = 1
            if len(self.state) >= 3:
                self.reg_set.add(self.state[2])
            if len(self.state) == 4:
                self.reg_set.add(self.state[3])
            if len(self.state) > 4:
                print('bad state!')
                raise Exception('State too long')
            # if self.step_count >= 0 and self.is_aligned(3):
            #     print('---', self.step_count, '---')
            #     self.recursive_print(3)
            #     print('-'*50)
            self.step_count += 1
            if self.step_count == 4 ** len(self.level_step_count):
                self.level_step_count.append(0)
            for i in range(len(self.level_step_count)):
                if self.is_aligned(i):
                    self.level_step_count[i] += 1
                else:
                    break
            self.step()
            if pow10(self.step_count):
                print(' >> Step ', self.step_count)
                print('Registers:     ', len(self.reg_set))
                print('Symbols:       ', len(self.info_set))
                print('Tagged States: ', len(self.tagged_state_count))
                
            if self.step_count == 1e6:
                break
        # common_tagged_states = sorted(list(self.tagged_state_count), key = lambda x: -self.tagged_state_count[x])
        # mode_count = {}
        # for k in self.tagged_state_count:
        #     if k[0] in mode_count:
        #         mode_count[k[0]] += self.tagged_state_count[k]
        #     else:
        #         mode_count[k[0]] = self.tagged_state_count[k]
        # for i in range(30):
        #     print(common_tagged_states[i], ' -- ', self.tagged_state_count[common_tagged_states[i]])
        # common_modes = sorted(list(mode_count), key = lambda x: -mode_count[x])
        # for k in common_modes:
        #     print(k, ' -- ', mode_count[k])

        # f = open('to_int_dict.txt', 'w', encoding='utf-8')
        # for i, state in enumerate(self.tagged_state_count.keys()):
        #     f.write(str(i) + ':' + str(state) + '\n')
        # f.write('NEXT\n')
        # for i, reg in enumerate(self.reg_set):
        #     f.write(str(i) + ':' + str(reg)+ '\n')
        # f.write('NEXT\n')
        # for i, symbol in enumerate(self.info_set):
        #     f.write(str(i) + ':' + str(symbol)+ '\n')
        print(self.level_step_count)
        return self.tape

    def simple_state_transition(self, simple_state, info):
        # Now checking immediately when reading state
        # if simple_state == BLANK:
        #     return (('mutate', (-1, -1, 2, True, 0)), ('read_state', None), BLANK)
        mode, *_ = simple_state
        if mode == 'calculate_transition':
            raise Exception('Calculate regress')
        # Make sure these sentinels aren't used as actual values!
        nstate, write, mov_dir = self.self_sim_transition((*simple_state, (1, None), (2, None)), info)
        new_mode, new_tags, new_reg1, new_reg2, *_ = *nstate, None, None, None
        new_state = (new_mode, new_tags)
        # Currently only end up with disordered registers if carrying a new state
        # TODO clean up this whole register mess - or make it a spec!
        if new_mode in [1, 2]:
            return (('mutate', (new_mode, 0, 2, False, mov_dir)), None, write)
        if write in [(1, None), (2, None)]:
            return (('mutate', (write[0], 3, 2, True, mov_dir)), new_state, None)
        if new_reg1 == info:
            return (('mutate', (3, 1, 2, True, mov_dir,)), new_state, write)
        if new_reg2 == info:
            return (('mutate', (3, 2, 2, True, mov_dir)), new_state, write)
        return (('mutate', (-1, -1, 2, True, mov_dir)), new_state, write)

    def self_sim_transition(self, state, info):
        mode, tags, reg1, reg2, *_ = *state, None, None, None
        if mode == 'read_state':
            if info == BLANK:
                return (('read_state', None), ('read_state', None), 0)
            if type(info) == tuple and info[0] == 'calculate_transition':
                return (('read_info', (0, True)), None, 1)
            else:
                return (('read_info', (0, False), info), None, 1)
        if mode == 'read_info':
            STEP, IS_CALC = list(range(2))
            step, is_calc = tags
            new_tags = list(tags)
            if step == 0:
                new_tags[STEP] = 1
                if is_calc:
                    return ((mode, tuple(new_tags), info), None, 1)
                else:
                    return ((mode, tuple(new_tags), reg1), None, 1)
            if step == 1:
                new_tags[STEP] = 2
                if is_calc:
                    return ((mode, tuple(new_tags), reg1), 'to_reg', 1)
                else:
                    return ((mode, tuple(new_tags), reg1), None, 1)
            if step == 2:
                return (('calculate_transition', None, reg1), None, 0)
        if mode == 'calculate_transition':
            mutate_ins, next_state, write = self.simple_state_transition(reg1, info)
            return (('write', 0, mutate_ins, next_state or BLANK), write, -1)
        if mode == 'write':
            step = tags
            if step == 0:
                if info == 'to_reg':
                    return (('write', 1, reg1), reg2, -1)
                else:
                    # This double register move is hard-coded in mutate
                    # Reg1 will always be a mutate instruction
                    return ((*reg1, reg2), None, 0)
            if step == 1:
                return (('write', 2), reg1, -1)
            if step == 2:
                return (('move', (0, 0, -1)), ('write', 0), 0)
        # I should always be initialized to 2, since that's where write will leave it
        # Copies only after new info is written - break into two states if you'd like to keep the original
        if mode == 'mutate':
            X, Y, I, WRITE_NEW_STATE, MOV_DIR = range(5)
            x, y, i, write_new_state, mov_dir = tags
            new_tags = list(tags)
            if i == -2:
                # Blank the register
                new_tags[I] = x
                new_tags[X] = -1
                return ((mode, tuple(new_tags), reg1, reg2), BLANK, 0)
            if i == -1:
                # Scoot over the other register
                new_tags[I] = 3
                return ((mode, tuple(new_tags), reg2), None, 0)
            if x != -1:
                if i < x:
                    new_tags[I] += 1
                    return ((mode, tuple(new_tags), reg1), None, 1)
                if i > x:
                    new_tags[I] -= 1
                    return ((mode, tuple(new_tags), reg1), None, -1)
                if i == x:
                    # We're copying out of a register - wipe it! (in two steps, of course)
                    if x in [1, 2]:
                        new_tags[I] = -2
                        return ((mode, tuple(new_tags), reg1, info), None, 0)
                    else:
                        new_tags[X] = -1
                        return ((mode, tuple(new_tags), reg1, info), None, 0)
            elif y != -1:
                if i < y:
                    new_tags[I] += 1
                    return ((mode, tuple(new_tags), reg1, reg2), None, 1)
                if i > y:
                    new_tags[I] -= 1
                    return ((mode, tuple(new_tags), reg1, reg2), None, -1)
                if i == y:
                    # We're copying reg1 into state. Now move 2 into 1: TODO (tidy)
                    if y == 0:
                        new_tags[X] = 2
                        new_tags[Y] = 1
                        return ((mode, tuple(new_tags), reg1), reg2, 0)
                    new_tags[Y] = -1
                    return ((mode, tuple(new_tags), reg1), reg2, 0)
            else:
                if i > 0:
                    new_tags[I] -= 1
                    return ((mode, tuple(new_tags), reg1), None, -1)
                else:
                    if write_new_state:
                        return (('move', (0, 0, mov_dir)), reg1, 0)
                    else:
                        return (('move', (0, 0, mov_dir)), None, 0)
        if mode == 'move':
            SWING, STEPS, MOV_DIR = range(3)
            swing, steps, mov_dir = tags
            new_tags = list(tags)
            if mov_dir == 0:
                return (('read_state', None), None, 0)
            if swing == 3:
                if mov_dir == 1:
                    if steps == 0:
                        new_tags[STEPS] += 1
                        return ((mode, tuple(new_tags)), None, 1)
                    return (('read_state', None), None, 0)
                else:
                    if steps == 6:
                        return (('read_state', None), None, -1)
                    else:
                        new_tags[STEPS] += 1
                        return ((mode, tuple(new_tags)), None, -1)
            else:
                new_tags[STEPS] += 1
                if steps == 0:
                    if info not in [BLANK, 'a', 'b', 'c']:
                        return ((mode, tuple(new_tags), info), None, 0)
                    else:
                        return ((mode, tuple(new_tags), BLANK), None, 0)
                if steps == 1:
                    BLANK_LEAVE = 'abc'[swing]
                    return ((mode, tuple(new_tags), reg1), BLANK_LEAVE, mov_dir)
                if 2 <= steps <= 4:
                    return ((mode, tuple(new_tags), reg1), None, mov_dir)
                if steps == 5:
                    return ((mode, tuple(new_tags)), reg1, -mov_dir)
                if 6 <= steps <= 8:
                    return ((mode, tuple(new_tags)), None, -mov_dir)
                if steps == 9:
                    new_tags[STEPS] = 0
                    new_tags[SWING] += 1
                    return ((mode, tuple(new_tags)), None, 1)
        print('end of trans!', state, info)

BLANK = 0
self_sim_tm = SelfSimTM([BLANK], ('read_state', None), None)
self_sim_tm.run()