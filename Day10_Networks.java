import java.util.*;

public class Day10_Networks {
    static long ipToLong(String ip) {
        long value = 0;
        for (String part : ip.split("\\.")) value = (value << 8) | Integer.parseInt(part);
        return value;
    }
    static String toIp(long value) {
        return ((value >>> 24) & 255) + "." + ((value >>> 16) & 255) + "." +
            ((value >>> 8) & 255) + "." + (value & 255);
    }
    static long mask(int prefix) { return prefix == 0 ? 0 : (0xFFFF_FFFFL << (32 - prefix)) & 0xFFFF_FFFFL; }
    static int evenParityBit(String bits) {
        int ones = 0; for (char bit : bits.toCharArray()) if (bit == '1') ones++;
        return ones % 2;
    }
    public static void main(String[] args) {
        long ip = ipToLong("192.168.1.70"), mask = mask(26);
        long network = ip & mask, broadcast = network | (~mask & 0xFFFF_FFFFL);
        if (!toIp(network).equals("192.168.1.64") || !toIp(broadcast).equals("192.168.1.127") || evenParityBit("1011") != 1)
            throw new AssertionError("network calculation");
        System.out.println("network: " + toIp(network) + " | broadcast: " + toIp(broadcast) + " | addresses: 64");
        System.out.println("even parity bit for 1011: " + evenParityBit("1011"));
    }
}
