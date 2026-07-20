// Self-contained fixture for the $assert executor (dipdoc.py runAsserts).
// Framework-free on purpose: the symbols must resolve at module top level.

/**
 * @description Adds two numbers.
 * @param {number} a first
 * @param {number} b second
 * @return {number} the sum
 * $assert equal params(2, 3) result(5) two plus three
 * $assert not equal params(2, 2) result(5) negation works
 * $assert strictEqual params(0, 0) result(0)
 */
function add(a, b) {
	return a + b;
}

/**
 * @description Returns the receiver's value; exercises this() binding.
 * $prepare var ctx = { value: 7 };
 * $assert equal this(ctx) result(7) this-binding works
 * $assert equal params() result(999) intentionally wrong, must FAIL
 */
function getValue() {
	return this.value;
}
