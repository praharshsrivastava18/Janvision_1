public class Day02_LinearAlgebraProbability {
    static int[][] multiply(int[][] a, int[][] b) {
        int[][] result = new int[a.length][b[0].length];
        for (int i = 0; i < a.length; i++)
            for (int j = 0; j < b[0].length; j++)
                for (int k = 0; k < b.length; k++) result[i][j] += a[i][k] * b[k][j];
        return result;
    }
    public static void main(String[] args) {
        int[][] result = multiply(new int[][]{{1, 2}, {3, 4}}, new int[][]{{2, 0}, {1, 2}});
        if (result[0][0] != 4 || result[0][1] != 4 || result[1][0] != 10 || result[1][1] != 8)
            throw new AssertionError("matrix product");
        double prior = 0.01, sensitivity = 0.95, falsePositive = 0.05;
        double posterior = sensitivity * prior /
            (sensitivity * prior + falsePositive * (1 - prior));
        if (Math.abs(posterior - 0.161 - 0.0) > 0.001) throw new AssertionError(posterior);
        System.out.println("A x B: [[4, 4], [10, 8]]");
        System.out.printf("P(condition | positive): %.4f%n", posterior);
    }
}
