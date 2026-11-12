import java.util.*;

public class Day03_DigitalLogic {
    static int[] fullAdder(int a, int b, int carryIn) {
        int total = a + b + carryIn;
        return new int[]{total % 2, total / 2};
    }
    static int twosComplement(int value, int bits) {
        int mask = (1 << bits) - 1;
        return (~value + 1) & mask;
    }
    public static void main(String[] args) {
        List<String> rows = new ArrayList<>();
        for (int a = 0; a <= 1; a++) for (int b = 0; b <= 1; b++)
            for (int cin = 0; cin <= 1; cin++) {
                int[] out = fullAdder(a, b, cin);
                if (a + b + cin != out[0] + 2 * out[1]) throw new AssertionError();
                rows.add("(" + a + "," + b + "," + cin + "," + out[0] + "," + out[1] + ")");
            }
        if (twosComplement(5, 8) != 251) throw new AssertionError("two's complement");
        System.out.println("(a,b,cin,sum,cout): " + rows);
        System.out.println("-5 in 8-bit two's complement: " +
            String.format("%8s", Integer.toBinaryString(twosComplement(5, 8))).replace(' ', '0'));
    }
}
