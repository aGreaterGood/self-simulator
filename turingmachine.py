# 1 bi-directional tape. transition as function
# Head initialized at 0

import random as rnd

class TuringMachine:
    def __init__(self, tape, transition_fun, start, end, blank, alphabet=None, state_list=None):
        # Initialize the tape and state, save the transition
        # Maintain dedicated start, end, and blank states, as well as a full alphabet and statelist
        self.tape = tape
        self.head_pos = 0
        self.transition = transition_fun
        self.start = start
        self.state = start
        self.end = end
        self.blank = blank
        self.alphabet = alphabet
        self.state_list = state_list
        self.step_count = 0
        # For if the tape has to be expanded
        self.zero_pos = 0

    # Causes the Machine to advance one step
    def step(self):
        # Next state or write can return None == 'No Change'. Move must return 0.
        next_state, write, move = self.transition(self.state, self.tape[self.head_pos])
        if next_state is not None:
            self.state = next_state
        if write is not None:
            self.tape[self.head_pos] = write
        self.head_pos += move
        # This extends the tape if we run off it, moving the head position and the zero position as needed
        if self.head_pos >= len(self.tape):
            self.tape = self.tape + [self.blank] * len(self.tape)
        if self.head_pos < 0:
            self.head_pos += len(self.tape)
            self.zero_pos += len(self.tape)
            self.tape = [self.blank] * len(self.tape) + self.tape

    # Causes the machine to run until it hits 'end'. Option to print at each step
    def run(self, verbose=False):
        while(self.state != self.end):
            if self.step_count % 1e6 == 0 and self.step_count > 0:
                print('Running - ', self.step_count)
            self.step_count += 1
            self.step()
            if verbose:
                print(''.join(str(c) for c in self.tape))
                print(self.state, ' -- ', self.head_pos)
        return self.tape


# Version of the Turing machine which occasionally has a faulty transition
class NoisyTuringMachine(TuringMachine):
    def __init__(self, *args, noise=0, state_list=None, alphabet=None):
        super().__init__(*args)
        self.noise = noise
        self.state_list = state_list
        self.alphabet = alphabet
    
    def run(self):
        while(self.state != self.end):
            if self.step_count % 1e6 == 0:
                print('Running - ', self.step_count)
            self.step_count += 1
            if rnd.random() < self.noise:
                random_state = rnd.choice(self.state_list)
                random_write = rnd.choice(self.alphabet)
                random_mov = rnd.choice([-1, 0, 1])
                self.tape[self.head_pos] = random_write
                self.state = random_state
                self.head_pos += random_mov
                if self.head_pos >= len(self.tape):
                    self.tape = self.tape + [self.blank] * len(self.tape)
                if self.head_pos < 0:
                    self.head_pos += len(self.tape)
                    self.tape = [self.blank] * len(self.tape) + self.tape
            else:
                self.step()
            # print(''.join(self.tape))
        return self.tape


# TEST CASES
# Busy beaver 5 test case, well known TM with complicated behavior
BB5_dict = {
    'A': [('R', 1, 'B'), ('L', 1, 'C')],
    'B': [('R', 1, 'C'), ('R', 1, 'B')],
    'C': [('R', 1, 'D'), ('L', 0, 'E')],
    'D': [('L', 1, 'A'), ('L', 1, 'D')],
    'E': [('R', 1, 'end'), ('L', 0, 'A')]
}
def BB5_transition(state, symbol):
    res = BB5_dict[state][symbol]
    if res[0] == 'R':
        m = 1
    else:
        m = -1
    return [res[2], res[1], m]

def test_TM_BB5():
    test_tape = [0]
    test_machine = TuringMachine(test_tape, BB5_transition, 'A', 'end', 0)
    print('PASSED:', sum(test_machine.run()) == 4098)

# Copy TM. Copies the string from between A and B to beyond X
copy_alphabet = ['A', 'B', 'X', '0', '1', '_', 'P']
copy_states = ['start', 'mv_x_r', 'x_p_write', 'mv_a_l', 'read', 'copy1r', 'copy0r',
        'shift_x_p_1', 'shift_x_p_0', 'copy1l', 'copy0l', 'erase_p', 'end']
def copy_transition(state, cell, suppress_bad_transition = True):
    if cell not in copy_alphabet:
        print(cell)
    assert cell in copy_alphabet, 'Bad Cell: ' + str(cell)
    assert state in copy_states, 'Bad State: ' + str(state)
    if state == 'start':
        return ('mv_x_r', None, 1)
    if state == 'mv_x_r':
        if cell == 'X':
            return ('x_p_write', None, 1)
        else:
            return ('mv_x_r', None, 1)
    if state == 'x_p_write':
        return ('mv_a_l', 'P', -1)
    if state == 'mv_a_l':
        if cell == 'A':
            return ('read', None, 1)
        else:
            return ('mv_a_l', None, -1)
    if state == 'read':
        if cell == '1':
            return ('copy1r', 'P', 1)
        elif cell == '0':
            return ('copy0r', 'P', 1)
        elif cell == 'B':
            return ('erase_p', None, 1)
    if state == 'copy1r':
        if cell == 'P':
            return ('shift_x_p_1', '1', 1)
        else:
            return ('copy1r', None, 1)
    if state == 'copy0r':
        if cell == 'P':
            return ('shift_x_p_0', '0', 1)
        else:
            return ('copy0r', None, 1)
    if state == 'shift_x_p_1':
        return ('copy1l', 'P', -1)
    if state == 'shift_x_p_0':
        return ('copy0l', 'P', -1)
    if state == 'copy1l':
        if cell == 'P':
            return ('read', '1', 1)
        else:
            return ('copy1l', None, -1)
    if state == 'copy0l':
        if cell == 'P':
            return ('read', '0', 1)
        else:
            return ('copy0l', None, -1)
    if state == 'erase_p':
        if cell == 'P':
            return ('end', '_', 0)
        else:
            return ('erase_p', None, 1)
    if state == 'end':
        return ('end', None, 0)
    if suppress_bad_transition:
        return (None, None, 0)
    else:
        print(state)
        print(cell)
        raise Exception('Invalid transition')

def test_string_copy(test_str = None):
    if test_str is None:
        s = 'A00110110111010111010100101001000101001010101B___________________X'
    else:
        s = 'A' + test_str + 'B' + '_'*3 + 'X'
    starting_tape = list(s)
    copy_TM = TuringMachine(starting_tape, copy_transition, 'start', 'end', '_')
    # copy_TM = NoisyTuringMachine(starting_tape, copy_transition, 'start', 'end', '_',
    #     noise=.05, alphabet=copy_alphabet, state_list=copy_states)
    res = copy_TM.run()
    print(''.join(res))
    print('PASSED: ', res[res.index('A')+1:res.index('B')] == res[res.index('X')+1:res.index('X')+res.index('B')-res.index('A')])

def main():
    print('RANDOM STR COPY TEST')
    s = ''
    for i in range(rnd.randint(1, 50)):
        s += str(rnd.randint(0, 1))
    test_string_copy(s)
    print('BB5 TEST')
    test_TM_BB5()

if __name__ == '__main__':
    main()
