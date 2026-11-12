import java.util.*;

public class Day12_CompilerParser {
    static List<String> tokenize(String s) {
        List<String> out = new ArrayList<>();
        for (int i = 0; i < s.length();) {
            char c = s.charAt(i);
            if (Character.isWhitespace(c)) { i++; continue; }
            if (Character.isDigit(c)) {
                int start = i++; while (i < s.length() && Character.isDigit(s.charAt(i))) i++;
                out.add(s.substring(start, i));
            } else { out.add(String.valueOf(c)); i++; }
        }
        return out;
    }
    static class Parser {
        List<String> t; int i = 0; Parser(List<String> t) { this.t = t; }
        String take() { return t.get(i++); }
        List<String> factor() {
            String token = take();
            if (token.equals("(")) { List<String> out = expr();
                if (!take().equals(")")) throw new IllegalArgumentException("expected )"); return out; }
            if (!token.matches("\\d+")) throw new IllegalArgumentException("expected number");
            return new ArrayList<>(List.of(token));
        }
        List<String> term() {
            List<String> out = factor();
            while (i < t.size() && (t.get(i).equals("*") || t.get(i).equals("/"))) {
                String op = take(); out.addAll(factor()); out.add(op);
            } return out;
        }
        List<String> expr() {
            List<String> out = term();
            while (i < t.size() && (t.get(i).equals("+") || t.get(i).equals("-"))) {
                String op = take(); out.addAll(term()); out.add(op);
            } return out;
        }
    }
    public static void main(String[] args) {
        List<String> tokens = tokenize("2 + 3 * (4 - 1)");
        List<String> postfix = new Parser(tokens).expr();
        List<String> expected = List.of("2", "3", "4", "1", "-", "*", "+");
        if (!postfix.equals(expected)) throw new AssertionError(postfix);
        System.out.println("tokens: " + tokens + " | postfix: " + postfix);
    }
}
