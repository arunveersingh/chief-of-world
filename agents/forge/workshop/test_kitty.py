import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from kitty import resolve, shares
# one leaver: 10 * 40 // 40 = 10
assert shares(40, {"Asha": 20, "Ben": 10, "Cy": 10}, ["Ben"]) == {"Ben": 10}
# two leavers measured on one snapshot (LAW-0020): 7 in pot, 6/4/2/1 put in -> 3 and 2
assert shares(7, {"f": 6, "l": 4, "w": 2, "a": 1}, ["f", "l"]) == {"f": 3, "l": 2}
# leaver paid first, then a spend capped at half of what's left (Ash's tick-23 case in household terms)
put = {"A": 6, "B": 4, "C": 2, "D": 1}
paid, out, left = resolve(7, put, list(put) + ["S"], ["A"], [("tool", 3, "B", ["C", "D", "S"])])
assert paid == {"A": 3} and out[0][2] is False and "cap" in out[0][3][0] and left == 4
# a spend with a majority of other contributors and a stranger yes passes
paid, out, left = resolve(40, {"Asha": 20, "Ben": 10, "Cy": 10}, ["Asha", "Ben", "Cy", "Dev"], [], [("paint", 15, "Asha", ["Ben", "Cy", "Dev"])])
assert out[0][2] and left == 25
# no stranger yes -> refused; requester's own yes never counts
_, out, _ = resolve(40, {"Asha": 20, "Ben": 10, "Cy": 10}, ["Asha", "Ben", "Cy", "Dev"], [], [("paint", 15, "Asha", ["Asha", "Ben", "Cy"])])
assert not out[0][2] and any("never paid in" in w for w in out[0][3])
# a leaver stays a contributor at zero: not counted for approval, and not a stranger either
_, out, _ = resolve(40, {"Asha": 20, "Ben": 10, "Cy": 10}, ["Asha", "Ben", "Cy"], ["Ben"], [("paint", 15, "Asha", ["Ben", "Cy"])])
assert out[0][2], out          # Cy alone is all the other contributors; there are no strangers
print("all kitty tests pass")
