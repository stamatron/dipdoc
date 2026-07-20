# Self-contained fixture for the $assert executor (dipdoc.py runAsserts).
# Doc blocks precede the declaration; symbols resolve at module top level.

"""
@description Adds two numbers.
@param {int} a first
@param {int} b second
@return {int} the sum
$assert equal params(2, 3) result(5) two plus three
$assert not equal params(2, 2) result(5) negation works
$assert equal params(0, 0) result(0)
"""
def add(a, b):
	return a + b


"""
@description Returns the receiver's value; exercises this() binding.
$prepare ctx = type('C', (), {'value': 7})()
$assert equal this(ctx) result(7) this-binding works
"""
def get_value(self):
	return self.value


def mul(a, b):
	"""
	@description Multiplies; documented in-body (docstring style), not above.
	@param {int} a first
	@param {int} b second
	$assert equal params(2, 3) result(6) two times three
	$assert equal params(0, 5) result(0)
	"""
	return a * b
