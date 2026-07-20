# Self-contained fixture for the $assert executor (dipdoc.py runAsserts).
# Doc blocks precede the declaration; symbols resolve at module top level.

=begin
@description Adds two numbers.
@param {Integer} a first
@param {Integer} b second
@return {Integer} the sum
$assert equal params(2, 3) result(5) two plus three
$assert not equal params(2, 2) result(5) negation works
$assert equal params(0, 0) result(0)
=end
def add(a, b)
	a + b
end

=begin
@description Returns the receiver's value; exercises this() binding.
$prepare ctx = Struct.new(:value).new(7)
$assert equal this(ctx) result(7) this-binding works
=end
def get_value(obj)
	obj.value
end
