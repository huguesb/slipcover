import pytest
from slipcover import slipcover as sc
import dis
import sys


#PYTHON_VERSION = sys.version_info[0:2]


def current_line():
    import inspect as i
    return i.getframeinfo(i.currentframe().f_back).lineno

def current_file():
    import inspect as i
    return i.getframeinfo(i.currentframe().f_back).filename

def from_set(s: set):
    return next(iter(s))

@pytest.fixture(autouse=True)
def clear_slipcover():
    # XXX have slipcover use an object, so that it's destroyed and this isn't needed?
    sc.clear()

def test_get_jumps():
    # FIXME breaks in 3.10 because only one jump is generated
    def foo(x):
        if x: print(True)
        else: print(False)

    code = foo.__code__.co_code
    jumps = sc.get_jumps(code)
    dis.dis(foo)
    assert 2 == len(jumps)

    j = jumps[0]
    assert 2 == j.length
    assert code[j.offset+j.length-2] == j.opcode
    assert (j.opcode in dis.hasjabs) or (j.opcode in dis.hasjrel)
    assert (j.opcode in dis.hasjrel) == j.is_relative
    # XXX check target

    j = jumps[1]
    assert 2 == j.length
    assert j.opcode == code[j.offset+j.length-2]
    assert (j.opcode in dis.hasjabs) or (j.opcode in dis.hasjrel)
    assert (j.opcode in dis.hasjrel) == j.is_relative
    # XXX check target

    assert jumps[0].offset < jumps[1].offset


# XXX test_get_jumps_ext_jumps

# Test case building rationale:
#
# There are relative and absolute jumps; both kinds have an offset (where
# the operation is located) and a target (absolute offset for the jump,
# resolved from the argument).
# 
# On forward jumps, an insertion can happen before the offset, at the offset,
# between the offset and the target, at the target, or after the target.
# On backward jumps, an insertion can happen before the target, between the
# target and the offset, at the offset, or after the offset.
#
# Jumps have an offset (op address) and a target (absolute jump address).
# There are relative and absolute jumps; absolute jumps may jump forward
# or backward.  In absolute forward jumps, the offset (op address) precedes
# the target and in backwards

def test_jump_adjust_abs_fw_before_offset():
    j = sc.JumpOp(100, 2, from_set(dis.hasjabs), arg=sc.offset2jump(108))
    j.adjust(90, 2)

    assert 102 == j.offset
    assert 2 == j.length
    assert 110 == j.target
    assert sc.offset2jump(108) != j.arg()

def test_jump_adjust_abs_fw_at_offset():
    j = sc.JumpOp(100, 2, from_set(dis.hasjabs), arg=sc.offset2jump(108))
    j.adjust(100, 2)

    assert 102 == j.offset
    assert 2 == j.length
    assert 110 == j.target
    assert sc.offset2jump(108) != j.arg()

def test_jump_adjust_abs_fw_after_offset_before_target():
    j = sc.JumpOp(100, 2, from_set(dis.hasjabs), arg=sc.offset2jump(108))
    j.adjust(105, 2)

    assert 100 == j.offset
    assert 2 == j.length
    assert 110 == j.target
    assert sc.offset2jump(108) != j.arg()

def test_jump_adjust_abs_fw_at_target():
    j = sc.JumpOp(100, 2, from_set(dis.hasjabs), arg=sc.offset2jump(108))
    j.adjust(108, 2)

    assert 100 == j.offset
    assert 2 == j.length
    assert 108 == j.target
    assert sc.offset2jump(108) == j.arg()

def test_jump_adjust_abs_fw_after_target():
    j = sc.JumpOp(100, 2, from_set(dis.hasjabs), arg=sc.offset2jump(108))
    j.adjust(110, 2)

    assert 100 == j.offset
    assert 2 == j.length
    assert 108 == j.target
    assert sc.offset2jump(108) == j.arg()

def test_jump_adjust_abs_bw_before_target():
    j = sc.JumpOp(100, 2, from_set(dis.hasjabs), arg=sc.offset2jump(90))
    j.adjust(50, 2)

    assert 102 == j.offset
    assert 2 == j.length
    assert 92 == j.target
    assert sc.offset2jump(90) != j.arg()

def test_jump_adjust_abs_bw_at_target():
    j = sc.JumpOp(100, 2, from_set(dis.hasjabs), arg=sc.offset2jump(90))
    j.adjust(90, 2)

    assert 102 == j.offset
    assert 2 == j.length
    assert 90 == j.target
    assert sc.offset2jump(90) == j.arg()

def test_jump_adjust_abs_bw_after_target_before_offset():
    j = sc.JumpOp(100, 2, from_set(dis.hasjabs), arg=sc.offset2jump(90))
    j.adjust(96, 2)

    assert 102 == j.offset
    assert 2 == j.length
    assert 90 == j.target
    assert sc.offset2jump(90) == j.arg()

def test_jump_adjust_abs_bw_at_offset():
    j = sc.JumpOp(100, 2, from_set(dis.hasjabs), arg=sc.offset2jump(90))
    j.adjust(100, 2)

    assert 102 == j.offset
    assert 2 == j.length
    assert 90 == j.target
    assert sc.offset2jump(90) == j.arg()

def test_jump_adjust_abs_bw_after_offset():
    j = sc.JumpOp(100, 2, from_set(dis.hasjabs), arg=sc.offset2jump(90))
    j.adjust(110, 2)

    assert 100 == j.offset
    assert 2 == j.length
    assert 90 == j.target
    assert sc.offset2jump(90) == j.arg()

def test_jump_adjust_rel_fw_before_offset():
    j = sc.JumpOp(100, 2, from_set(dis.hasjrel), arg=sc.offset2jump(30))
    j.adjust(90, 2)

    assert 102 == j.offset
    assert 2 == j.length
    assert 134 == j.target
    assert sc.offset2jump(30) == j.arg()

def test_jump_adjust_rel_fw_at_offset():
    j = sc.JumpOp(100, 2, from_set(dis.hasjrel), arg=sc.offset2jump(30))
    j.adjust(100, 2)

    assert 102 == j.offset
    assert 2 == j.length
    assert 134 == j.target
    assert sc.offset2jump(30) == j.arg()

def test_jump_adjust_rel_fw_after_offset_before_target():
    j = sc.JumpOp(100, 2, from_set(dis.hasjrel), arg=sc.offset2jump(30))
    j.adjust(105, 2)

    assert 100 == j.offset
    assert 2 == j.length
    assert 134 == j.target
    assert sc.offset2jump(30) != j.arg()

def test_jump_adjust_rel_fw_at_target():
    j = sc.JumpOp(100, 2, from_set(dis.hasjrel), arg=sc.offset2jump(30))
    j.adjust(132, 2)

    assert 100 == j.offset
    assert 2 == j.length
    assert 132 == j.target
    assert sc.offset2jump(30) == j.arg()

def test_jump_adjust_rel_fw_after_target():
    j = sc.JumpOp(100, 2, from_set(dis.hasjrel), arg=sc.offset2jump(30))
    j.adjust(140, 2)

    assert 100 == j.offset
    assert 2 == j.length
    assert 132 == j.target
    assert sc.offset2jump(30) == j.arg()


def test_make_lnotab():
    lines = [(0, 1),
             (6, 2),
             (50, 7),
             (350, 207),
             (361, 208),
             (370, 50)]


    lnotab = sc.make_lnotab(0, lines)

    assert [0, 1,
            6, 1,
            44, 5,
            255, 0,
            45, 127,
            0, 73,
            11, 1,
            9, -128,
            0, -30] == lnotab


def test_make_lnotab_compare():
    def foo(n):
        x = 0

        for i in range(n):
            x += (i+1)

        return x

    lines = list(dis.findlinestarts(foo.__code__))
    my_lnotab = sc.make_lnotab(foo.__code__.co_firstlineno, lines)

    assert list(foo.__code__.co_lnotab) == my_lnotab


def test_instrument():
    first_line = current_line()+2
    def foo(n):
        x = 0
        for i in range(n):
            x += (i+1)
        return x
    last_line = current_line()

    sc.instrument(foo)
#    dis.dis(foo)
    assert 6 == foo(3)

    assert {current_file(): {*range(first_line, last_line)}} == sc.get_coverage()


@pytest.mark.parametrize("N", [2, 20, 128, 256, 512, 4096, 8192, 65536, 131072])
def test_instrument_long_jump(N):
    # each 'if' adds a jump
    first_line = current_line()+2
    src = "x = 0\n" + \
          "while x == 0:\n" + \
          "  if x >= 0:\n" + \
          "    x += 1\n" * N

    code = compile(src, "foo", "exec")

    assert 2 <= len(sc.get_jumps(code.co_code))

    code = sc.instrument(code)
    exec(code, locals(), globals())
    assert N == x
    assert {"foo": {*range(1, 1+N+3)}} == sc.get_coverage()


def test_deinstrument():
    first_line = current_line()+2
    def foo(n):
        x = 0
        for i in range(n):
            x += (i+1)
        return x
    last_line = current_line()

    assert not sc.get_coverage()

    sc.instrument(foo)
    sc.deinstrument(foo, {*range(first_line, last_line)})
    assert 6 == foo(3)
    assert not sc.get_coverage()


def test_deinstrument_some():
    first_line = current_line()+2
    def foo(n):
        x = 0
        for i in range(n):
            x += (i+1)
        return x
    last_line = current_line()

    assert not sc.get_coverage()

    sc.instrument(foo)
    sc.deinstrument(foo, {first_line, last_line-1})

    assert 6 == foo(3)
    assert {current_file(): {*range(first_line+1, last_line-1)}} == sc.get_coverage()