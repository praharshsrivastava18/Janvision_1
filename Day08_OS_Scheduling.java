import java.util.*;

public class Day08_OS_Scheduling {
    static int[] fcfs(int[] bursts) {
        int clock = 0; int[] waits = new int[bursts.length];
        for (int i = 0; i < bursts.length; i++) { waits[i] = clock; clock += bursts[i]; }
        return new int[]{waits[0], waits[1], waits[2], clock};
    }
    static List<Integer> safeSequence(int available, int[][] allocation, int[][] need) {
        int work = available; boolean[] done = new boolean[need.length];
        List<Integer> sequence = new ArrayList<>();
        while (sequence.size() < need.length) {
            boolean progressed = false;
            for (int i = 0; i < need.length; i++) if (!done[i] && need[i][0] <= work) {
                work += allocation[i][0]; done[i] = true; sequence.add(i); progressed = true; break;
            }
            if (!progressed) return null;
        }
        return sequence;
    }
    public static void main(String[] args) {
        int[] fcfs = fcfs(new int[]{5, 3, 2});
        List<Integer> safe = safeSequence(1, new int[][]{{1}, {1}}, new int[][]{{2}, {0}});
        if (!Arrays.equals(fcfs, new int[]{0, 5, 8, 10}) || !safe.equals(List.of(1, 0)))
            throw new AssertionError("OS result");
        System.out.println("FCFS waiting: [0, 5, 8] | finish: 10 | safe sequence: " + safe);
    }
}
