public class Day11_TheoryOfComputation {
    static boolean endsWith01(String bits) {
        String state = "";
        for (char bit : bits.toCharArray()) {
            if (bit != '0' && bit != '1') return false;
            state = (state + bit).substring(Math.max(0, state.length() + 1 - 2));
        }
        return state.equals("01");
    }
    static boolean balancedParentheses(String text) {
        int depth = 0;
        for (char c : text.toCharArray()) {
            if (c == '(') depth++;
            else if (c == ')' && --depth < 0) return false;
        }
        return depth == 0;
    }
    public static void main(String[] args) {
        if (!endsWith01("1101") || endsWith01("1110") ||
            !balancedParentheses("(()())") || balancedParentheses("())("))
            throw new AssertionError("language test");
        System.out.println("DFA 1101: true | balanced (()()): true");
    }
}
